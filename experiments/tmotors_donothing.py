import numpy as np

from double_pendulum.controller.trajectory_following.feed_forward import FeedForwardController
from double_pendulum.experiments.hardware_control_loop_tmotors import run_experiment
from double_pendulum.model.symbolic_plant import SymbolicDoublePendulum
from double_pendulum.model.model_parameters import model_parameters


torque_limit = [5.0, 5.0]

# trajectory
dt = 0.005
t_final = 30.0
N = int(t_final / dt)
T_des = np.linspace(0, t_final, N+1)
u1 = np.zeros(N+1)
u2 = np.zeros(N+1)
U_des = np.array([u1, u2]).T

# measurement filter
# meas_noise_cut = 0.15
# meas_noise_vfilter = "lowpass"
# filter_kwargs = {"lowpass_alpha": [1., 1., 0.3, 0.3]}

# controller
controller = FeedForwardController(T=T_des,
                                   U=U_des,
                                   torque_limit=[0., 0.],
                                   num_break=40)

# controller.set_filter_args(filt=meas_noise_vfilter,
#          velocity_cut=meas_noise_cut,
#          filter_kwargs=filter_kwargs)


# gravity and friction compensation
#model_par_path = "../data/system_identification/identified_parameters/tmotors_v1.0/model_parameters.yml"
#mpar = model_parameters(filepath=model_par_path)
#plant = SymbolicDoublePendulum(model_pars=mpar)
#controller.set_gravity_compensation(plant=plant)

#controller.set_friction_compensation(damping=mpar.b, coulomb_fric=mpar.cf)
#controller.set_friction_compensation(damping=[0.005, 0.001], coulomb_fric=[0.093, 0.15])
#controller.set_friction_compensation(damping=[0.0, 0.01], coulomb_fric=[0.08, 0.04])

controller.init()

run_experiment(controller=controller,
               dt=dt,
               t_final=t_final,
               can_port="can0",
               motor_ids=[7, 8],
               tau_limit=torque_limit,
               save_dir="data/double-pendulum/tmotors/sysid")
