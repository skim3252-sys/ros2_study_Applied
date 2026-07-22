import rclpy as rp
from rclpy.executors import MultiThreadedExecutor

from my_first_package.my_publisher import TurtlesimPublisher
from my_first_package.my_subscriber import TurtlesimSubscriber

def main(args=None):
    rp.init(args=args)
    pub =TurtlesimPublisher()
    sub = TurtlesimSubscriber()
    executor = MultiThreadedExecutor()
    executor.add_node(pub)
    executor.add_node(sub)
    executor.spin()

    pub.destroy_node()
    sub.destroy_node()
    
    executor.shutdown()

if __name__ == '__main__':
    main() 
