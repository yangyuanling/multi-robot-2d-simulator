import math
from components.robots.interfaces.robot import Robot
from components.robots.models.differential_drive import DifferentialDrive
from components.robots.models.pose import Pose
from components import utilities
from components.config import CONFIG

# TODO: The robot has:
#   1. a state --> Pose
#   2. a interface --> Robot

# TODO: Add default values for the interface part
#   -> Here we do know that the kinematics are in fact for a differential drive
#   -> Geometry and sensor vary, so create defaults from which we can latter derive a configuration files


class DifferentialDriveRobot(Robot):

    def __init__(self, geometry, sensors, x=0.0, y=0.0, theta=0.0):
        super(DifferentialDriveRobot, self).__init__(geometry, DifferentialDrive(), sensors)
        self.pose = Pose(x, y, theta)
        self.id = Robot.next_id
        Robot.next_id += 1

        radius = self.geometry.radius
        for it, s in enumerate(self.sensors["proximity"]):
            s.set_id(it)
            s.compute_sensors_points((x, y), radius)
        
        self.neigh_list = []


# TODO: Implement the unicycle to differential drive transform
    def move(self, v, omega):
        r = self.geometry.wheel_radius
        l = self.geometry.robot_base
        max_speed = self.geometry.max_speed
        max_ang_speed = self.geometry.max_ang_speed

        # TODO: the total speed cannot be greater than the maximum possible speed --> limit it
        v = max(min(v, max_speed), -max_speed)
        omega = max(min(omega, max_ang_speed), -max_ang_speed)
        # if omega == 0:
        #     v = max(min(v, max_speed), -max_speed)
        # else:
        #     r = abs(v / omega)
        #     if (abs(v) >= max_speed):
        #         v = utilities.sgn(v) * max_speed / 2.0
        #         omega = utilities.sgn(omega) * v / r

        # TODO: Compute the left/right wheel angular speeds: (v, omega) --> (wl, wr)
        wl = (2 * v - omega * l) / (2 * r)
        wr = (2 * v + omega * l) / (2 * r)

        self.kinematics.set_drive_speeds(wl, wr)

    # TODO: You can compute a pose update in this world loop iteration in two ways:
    #   -> as in the course by using the encoder counts or
    #   -> directly from the angle in this world loop iteration
    #      (prefered -- since later on we might add noise to motion)
    #
    # TODO:  Alternatively we can burden the user with this, since we already provide encoder ticks.
    #   -> However, this also means that we will have to keep track for each of the
    #      robot poses in the world model, separately. This is required for representing the world state
    #      which gets drawn.

    # TODO: Move the code you write here as the last thing you do in the method below, then delete this method
    def __update_pose(self):
        # TODO: distances done by each wheel
        r = self.geometry.wheel_radius
        l = self.geometry.robot_base

        (angle_l, angle_r) = self.kinematics.get_wheel_angles()
        dl = angle_l * r
        dr = angle_r * r
        dc = (dl + dr) / 2

        # TODO: compute the new pose
        # get current pose
        (x, y) = self.pose.get_position()
        theta = self.pose.get_heading()

        # compute new pose
        x_new = x + dc * math.cos(theta)
        y_new = y + dc * math.sin(theta)
        theta_new = theta + (dr - dl) / l

        # TODO: the angle may require normalization/ do not use the atan2 trick because its very slow
        theta_new = utilities.normalize_angle(theta_new)

        # update pose
        self.pose.set_pose(x_new, y_new, theta_new)

        # update proximity sensors
        radius = self.geometry.radius
        for s in self.sensors["proximity"]:
            theta_s = utilities.normalize_angle(theta_new + s.initial_pos)
            s.get_pose().set_pose(radius * math.cos(theta_s), radius * math.sin(theta_s), theta_s)
            s.compute_sensors_points((x, y), radius)

    # TODO: This should update the differential drive part of the robot: angles, encoders, pose --> in this order
    def update(self, world_unit_time):
        # print("{} -> {}".format(self.id, self.neigh_list))

        # update diff drive angles
        self.kinematics.update(world_unit_time)

        # update diff drive encoders
        (angle_l, angle_r) = self.kinematics.get_wheel_angles()
        encoders = self.sensors["encoders"]
        encoders[0].update(angle_l)
        encoders[1].update(angle_r)

        # update pose
        self.__update_pose()

