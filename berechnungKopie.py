import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import streamlit as st
import streamlit.components.v1 as components
from scipy.optimize import fsolve
from scipy.optimize import least_squares
from database import save_joint_position

class Joint:
    def __init__(self, x, y, fixed=False):
        self.pos = np.array([x, y], dtype=float)
        self.fixed = fixed

class Link:
    def __init__(self, joint1, joint2):
        self.joint1 = joint1
        self.joint2 = joint2
        self.length = np.linalg.norm(joint1.pos - joint2.pos)

class Mechanism:
    def __init__(self, crank_speed):
        self.joints = []
        self.links = []
        self.crank_speed = crank_speed
        self.theta = 0
        self.trace = []
        self.selected_joint = 0
        self.line = None
        self.trace_line = None

    def add_joint(self, x, y, fixed=False):
        joint = Joint(x, y, fixed)
        self.joints.append(joint)
        return joint

    def add_link(self, joint1, joint2):
        link = Link(joint1, joint2)
        self.links.append(link)
        return link
    
    def set_tracked_joint(self, trace):
        t = trace
        self.selected_joint = t - 1

    def solve_positions(self):
        movable_joints = [j for j in self.joints if not j.fixed]

        if not movable_joints:
            return

        def equations(positions):
            positions = positions.reshape(-1, 2)
            eqs = []
            joint_positions = {joint: joint.pos.copy() for joint in self.joints if joint.fixed}

            for i, joint in enumerate(movable_joints):
                joint_positions[joint] = positions[i].copy()

            for link in self.links:
                pos1 = joint_positions[link.joint1]
                pos2 = joint_positions[link.joint2]

                if not hasattr(link, "length"):
                    link.length = np.linalg.norm(link.joint2.pos - link.joint1.pos)

                eqs.append((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2 - link.length**2)

            return np.array(eqs)

        initial_guess = np.array([j.pos for j in movable_joints]).flatten()
        initial_guess += np.random.normal(0, 0.01, size=initial_guess.shape)

        result = least_squares(equations, initial_guess, method='trf')

        if result.success:
            solved_positions = result.x.reshape(-1, 2)
            for i, joint in enumerate(movable_joints):
                joint.pos = solved_positions[i]
        else:
            print("Lösung nicht gefunden:", result.message)
            print("Residuen:", result.fun)

    def rotate_crank(self):
        self.theta = (self.theta - self.crank_speed) % (2 * np.pi)

        rotation_matrix = np.array([
            [np.cos(self.theta), -np.sin(self.theta)],
            [np.sin(self.theta), np.cos(self.theta)]
        ])

        origin = self.joints[0].pos
        crank_length = self.links[0].length

        self.joints[1].pos = origin + rotation_matrix @ np.array([crank_length, 0])

    def get_joint_positions(self):
        return [(joint.pos[0], joint.pos[1]) for joint in self.joints]
    
    def get_all_joint_positions(self):
        return [(pos[0], pos[1]) for pos in self.trace]

    def update(self, frame):
        self.theta = (self.theta + self.crank_speed) % (2 * np.pi)
        self.joints[1].pos = self.joints[0].pos + np.array([np.cos(self.theta), np.sin(self.theta)]) * self.links[0].length
        self.solve_positions()

        for i, joint in enumerate(self.joints):
            save_joint_position(frame, i, joint.pos[0], joint.pos[1], st.session_state.mechanism_name)

        link_xs = []
        link_ys = []
        for link in self.links:
            link_xs.extend([link.joint1.pos[0], link.joint2.pos[0], None])
            link_ys.extend([link.joint1.pos[1], link.joint2.pos[1], None])

        self.line.set_data(link_xs, link_ys)

        if self.trace:
            trace_xs, trace_ys = zip(*self.trace)
            self.trace_line.set_data(trace_xs, trace_ys)

        return self.line, self.trace_line

    def animate(self):
        fig, ax = plt.subplots()
        ax.set_xlim(-50, 50)
        ax.set_ylim(-50, 50)

        self.line, = ax.plot([], [], 'k-', lw=2)
        self.trace_line, = ax.plot([], [], 'r-', lw=1)

        ani = animation.FuncAnimation(fig, self.update, frames=360, interval=20, blit=False)
        return ani
