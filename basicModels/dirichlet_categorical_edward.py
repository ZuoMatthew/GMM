# -*- coding: UTF-8 -*-

"""
Dirichlet-Categorical model
Posterior inference with Edward MFVI
"""

import edward as ed
import numpy as np
import tensorflow as tf
from edward.models import Categorical, Dirichlet

N = 1000
K = 4

# Data generation
alpha = np.array([20., 30., 10., 10.])
pi = np.random.dirichlet(alpha)
zn_data = np.array([np.random.choice(K, 1, p=pi)[0] for n in xrange(N)])
print('pi={}'.format(pi))

# Prior definition
alpha_prior = tf.Variable(np.array([1., 1., 1., 1.]), trainable=False)

# Posterior inference MFVI
# Probabilistic model
pi = Dirichlet(alpha=alpha_prior)
zn = Categorical(p=tf.ones([N, 1], dtype=tf.float64)*pi)

# Variational model
qpi = Dirichlet(alpha=tf.nn.softplus(tf.Variable(
    tf.random_normal([K], dtype=tf.float64))))

# Inference
inference = ed.KLqp({pi: qpi}, data={zn: zn_data})
inference.run(n_iter=5000)

sess = ed.get_session()
print('qpi={}'.format(sess.run(qpi.mean())))