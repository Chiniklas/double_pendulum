import numpy as np

from double_pendulum.model.model_parameters import model_parameters
from double_pendulum.model.symbolic_plant import SymbolicDoublePendulum
from double_pendulum.controller.ilqr.ilqr_mpc_cpp import ILQRMPCCPPController
from double_pendulum.controller.pid.point_pid_controller import PointPIDController
from double_pendulum.controller.combined_controller import CombinedController
from double_pendulum.experiments.hardware_control_loop_tmotors import run_experiment
from double_pendulum.utils.wrap_angles import wrap_angles_top
from double_pendulum.utils.csv_trajectory import load_trajectory, trajectory_properties


cfric = [0., 0.]
motor_inertia = 0.
torque_limit = [0.0, 6.0]
torque_limit_pid = [6.0, 6.0]

model_par_path = "../data/system_identification/identified_parameters/tmotors_v1.0/model_parameters.yml"
#model_par_path = "../data/system_identification/identified_parameters/tmotors_v2.0/model_parameters_est.yml"
mpar = model_parameters()
mpar.load_yaml(model_par_path)
mpar.set_motor_inertia(motor_inertia)
# mpar.set_damping(damping)
mpar.set_cfric(cfric)
mpar.set_torque_limit(torque_limit)

# trajectory parameters
## tmotors v1.0
# csv_path = "../data/trajectories/acrobot/dircol/acrobot_tmotors_swingup_1000Hz.csv"

## tmotors v1.0
csv_path = "../data/trajectories/acrobot/ilqr_v1.0/trajectory.csv"

# tmotors v2.0
#csv_path = "../data/trajectories/acrobot/ilqr/trajectory.csv"

T, X, U = load_trajectory(csv_path, True)
dt, t_final, _, _ = trajectory_properties(T, X)

# swingup parameters
start = [0., 0., 0., 0.]
goal = [np.pi, 0., 0., 0.]

# controller parameters
N = 100
N_init = 1000
max_iter = 10
max_iter_init = 1000
regu_init = 1.
max_regu = 10000.
min_regu = 0.01
break_cost_redu = 1e-6
trajectory_stabilization = True
integrator = "runge_kutta"

u_prefac = 0.1
stage_prefac = 0.5
final_prefac = 10.
sCu = [u_prefac*9.97938814e+01, u_prefac*9.97938814e+01]
sCp = [stage_prefac*2.06969312e+01, stage_prefac*7.69967729e+01]
sCv = [stage_prefac*1.55726136e-01, stage_prefac*5.42226523e-00]
sCen = 0.0
fCp = [final_prefac*3.82623819e+02, final_prefac*7.05315590e+03]
fCv = [final_prefac*5.89790058e+01, final_prefac*9.01459500e+01]
fCen = 0.0

Kp = 5.
Ki = 1.0
Kd = 1.0

# switiching conditions
def condition1(t, x):
    return False

def condition2(t, x):
    goal = [np.pi, 0., 0., 0.]
    eps = [0.2, 0.2, 2.0, 2.0]

    y = wrap_angles_top(x)

    delta = np.abs(np.subtract(y, goal))
    max_diff = np.max(np.subtract(delta, eps))
    if max_diff > 0.:
        print(f"Stayed with TVLQR control in state x {x} at time {t}")
        return False
    else:
        print(f"Switched to PID control in state x {x} at time {t}")
        return True

# setup controller
controller1 = ILQRMPCCPPController(model_pars=mpar)
controller1.set_start(start)
controller1.set_goal(goal)
controller1.set_parameters(
        N=N,
        dt=dt,
        max_iter=max_iter,
        regu_init=regu_init,
        max_regu=max_regu,
        min_regu=min_regu,
        break_cost_redu=break_cost_redu,
        integrator=integrator,
        trajectory_stabilization=trajectory_stabilization)
controller1.set_cost_parameters(
        sCu=sCu,
        sCp=sCp,
        sCv=sCv,
        sCen=sCen,
        fCp=fCp,
        fCv=fCv,
        fCen=fCen)
controller1.load_init_traj(csv_path=csv_path)

controller2 = PointPIDController(
        torque_limit=torque_limit_pid,
        dt=dt)
controller2.set_parameters(
        Kp=Kp,
        Ki=Ki,
        Kd=Kd)
controller2.set_goal(goal)

controller = CombinedController(
        controller1=controller1,
        controller2=controller2,
        condition1=condition1,
        condition2=condition2)

# gravity and friction compensation
model_par_path = "../data/system_identification/identified_parameters/tmotors_v1.0/model_parameters.yml"
mpar = model_parameters(filepath=model_par_path)
plant = SymbolicDoublePendulum(model_pars=mpar)
#controller.set_gravity_compensation(plant=plant)

#controller.set_friction_compensation(damping=mpar.b, coulomb_fric=mpar.cf)
#controller.set_friction_compensation(damping=[0.005, 0.001], coulomb_fric=[0.093, 0.15])
controller.set_friction_compensation(damping=[0.0, 0.01], coulomb_fric=[0.08, 0.04])
controller.init()

# run experiment
run_experiment(controller=controller,
               dt=dt,
               t_final=t_final,
               can_port="can0",
               motor_ids=[7, 8],
               tau_limit=torque_limit,
               save_dir="data/acrobot/tmotors/ilqr_pid_results")
