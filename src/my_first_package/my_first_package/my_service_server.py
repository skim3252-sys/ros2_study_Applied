from my_first_package_msgs.srv import MultiSpawn
import rclpy as rp
from rclpy.node import Node
from turtlesim.srv import TeleportAbsolute
from turtlesim.srv import Spawn
import numpy as np
from numpy import cos, sin
import time

class MultiSpawning(Node):
    def __init__(self):
        super().__init__('multi_spawn') # node 이름 / multi_spawn : service 이름
        self.server = self.create_service(MultiSpawn, 'multi_spawn', self.callback_service)

        # client를 따로 빼서 서비스와 연결
        self.teleport = self.create_client(TeleportAbsolute, '/turtle1/teleport_absolute')
        self.spawn = self.create_client(Spawn, 'spawn')

        self.req_teleport = TeleportAbsolute.Request()
        self.req_spawn = Spawn.Request()

        self.center_x = 5.54
        self.center_y = 5.54

    def calc_position(self, n, r):
        gap_theta = 2*np.pi /n
        theta = [gap_theta * i for i in range(n)]
        x = [r*cos(th) for th in theta]
        y = [r*sin(th) for th in theta]

        return x, y, theta


    # multi_spawn 서비스에  /turtle1/teleport_absolute 서비스 연결
    def callback_service(self,request,response):
        print('Request : ', request)
        #Request 전용 변수 - 값 대입
        self.req_teleport.x = 4.
        self.req_teleport.y = 4.

        x, y, theta = self.calc_position(request.num, 3)

        for n in range(len(theta)):
            self.req_spawn.x = x[n] + self.center_x
            self.req_spawn.y = y[n] + self.center_y
            self.req_spawn.theta = theta[n]

            self.spawn.call_async(self.req_spawn)
            time.sleep(0.5)
        self.teleport.call_async(self.req_teleport) #client에서 call 진행

        response.x = x
        response.y = y
        response.theta = theta
        

        return response

def main(args=None):
    rp.init(args=args)
    multi_spawn = MultiSpawning() # 객체 이름 : multi_spawn
    rp.spin(multi_spawn)
    rp.shutdown()

if __name__ == '__main__':
    main()