import rclpy as rp
from rclpy.action import ActionServer
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
import time
import math
from turtlesim.msg import Pose
from geometry_msgs.msg import Twist
from my_first_package.my_subscriber import TurtlesimSubscriber
# action msgs
from my_first_package_msgs.action import DistTurtle
# 실시간 parameter 변경 / 확인을 위한 msg
from rcl_interfaces.msg import SetParametersResult
#rqt -> sliding_scale 를 통해 parameter 값을 실시간으로 바꾸고 확인 용
from rcl_interfaces.msg import ParameterDescriptor, FloatingPointRange

# ── 액션 서버 노드 ─────────────────────────────────────────────
class DistTurtleServer(Node):
    def __init__(self):
        super().__init__('dist_turtle_action_server')
        self.total_dist = 0.0          # 누적 이동 거리
        self.is_first_time = True      # 목표 시작 첫 프레임 여부
        self.current_pose = Pose()     # 구독자가 갱신해 주는 현재 위치
        self.previous_pose = Pose()    # 직전 프레임 위치

        # parameter description for rqt sliding_scale (declare 전에 먼저 정의)
        param_desc_quantile = ParameterDescriptor(
            description='quantile_time description',
            floating_point_range=[FloatingPointRange(from_value=0.0, to_value=1.0, step=0.01)]
        )
        param_desc_almost_goal = ParameterDescriptor(
            description='almost_goal_time description',
            floating_point_range=[FloatingPointRange(from_value=0.0, to_value=10.0, step=0.1)]
        )

        self.declare_parameter('quantile_time', 0.5, param_desc_quantile)
        self.declare_parameter('almost_goal_time', 2.0, param_desc_almost_goal)
        ## ros2 parameter server 에서 quantile_time, almost_goal_time 값을 가져와 변수화
        (quantile_time, almost_goal_time) = self.get_parameters(['quantile_time', 'almost_goal_time'])
        self.quantile_time = quantile_time.value
        self.almost_goal_time = almost_goal_time.value

        self.get_logger().info("quantile_time: {}, almost_goal_time: {}"
                               .format(quantile_time.value, almost_goal_time.value))

        # parameter 값이 바뀌면 콜백함수 호출
        self.add_on_set_parameters_callback(self.parameter_callback)
        

        self.get_logger().info("DistTurtle Action Server has been started.")

        #cmd, action server 생성
        self.publisher = self.create_publisher(Twist, 'turtle1/cmd_vel', 10)
        self.action_server = ActionServer(
            self,
            DistTurtle,
            'dist_turtle',
            self.execute_callback)

    def parameter_callback(self, params):
            for param in params:
                if param.name == 'quantile_time':
                    self.quantile_time = param.value
                elif param.name == 'almost_goal_time':
                    self.almost_goal_time = param.value
            self.get_logger().info(f"Parameters updated: quantile_time={self.quantile_time}," 
                                   f" almost_goal_time={self.almost_goal_time}")
            return SetParametersResult(successful=True)
    
    # 직전 위치와 현재 위치 사이의 이동 거리를 계산
    def calc_diff_pose(self):
        if self.is_first_time:
            self.previous_pose.x = self.current_pose.x
            self.previous_pose.y = self.current_pose.y
            self.is_first_time = False

        diff_dist = math.sqrt(
            (self.current_pose.x - self.previous_pose.x) ** 2
            + (self.current_pose.y - self.previous_pose.y) ** 2)

        self.previous_pose = self.current_pose
        return diff_dist

    # 목표가 들어오면 실행되는 콜백. 목표 거리에 도달할 때까지 반복한다.
    def execute_callback(self, goal_handle):
        feedback_msg = DistTurtle.Feedback()

        msg = Twist()
        msg.linear.x = goal_handle.request.linear_x
        msg.angular.z = goal_handle.request.angular_z

        while True:
            self.total_dist += self.calc_diff_pose()
            feedback_msg.remained_dist = goal_handle.request.dist - self.total_dist          
            goal_handle.publish_feedback(feedback_msg)   # 남은 거리 피드백
            self.publisher.publish(msg)                  # 거북이에게 속도 명령

            self.get_logger().info(f"Feedback: remained_dist={feedback_msg.remained_dist:.2f},total_dist={self.total_dist:.2f}")
            tmp = feedback_msg.remained_dist - goal_handle.request.dist * self.quantile_time
            tmp = abs(tmp)
            if tmp < 0.02:
                output_msg = "turtle passed the " + str(self.quantile_time * 100) + "% of the distance"
                output_msg += " : " + str(tmp)
                self.get_logger().info(output_msg)


            time.sleep(0.01)


            if feedback_msg.remained_dist <= 0.2:        # 목표 도달
                break

        goal_handle.succeed()
        result = DistTurtle.Result()
        result.pos_x = self.current_pose.x
        result.pos_y = self.current_pose.y
        result.pos_theta = self.current_pose.theta
        result.result_dist = self.total_dist

        # 다음 목표를 위해 상태 초기화
        self.total_dist = 0.0
        self.is_first_time = True
        return result


# ── 위치 구독 노드 ─────────────────────────────────────────────
# /turtle1/pose 를 구독해서 액션 서버의 current_pose 를 계속 갱신한다.
class TurtleSubForAction(TurtlesimSubscriber):
    def __init__(self, ac_server):
        super().__init__()
        self.ac_server = ac_server

    def callback(self, msg):
        self.ac_server.current_pose = msg


def main(args=None):
    rp.init(args=args)
    ac = DistTurtleServer()
    sub = TurtleSubForAction(ac_server=ac)

    # 두 노드를 한 프로세스에서 동시에 돌리기 위해 멀티스레드 실행기 사용
    executor = MultiThreadedExecutor()
    executor.add_node(ac)
    executor.add_node(sub)
    try:
        executor.spin()
    finally:
        ac.destroy_node()
        sub.destroy_node()
        executor.shutdown()
        rp.shutdown()


if __name__ == '__main__':
    main()
