# -*- coding: UTF-8 -*-

"""
Coordinate Ascent Variational Inference
process to approximate an Univariate Gaussian
"""

import math
import argparse
import numpy as np
from time import time
import tensorflow as tf

parser = argparse.ArgumentParser(description='CAVI in Univariate Gaussian')
parser.add_argument('-maxIter', metavar='maxIter', type=int, default=10000000)
parser.add_argument('-nElements', metavar='nElements', type=int, default=100)
parser.add_argument('--timing', dest='timing', action='store_true')
parser.add_argument('--no-timing', dest='timing', action='store_false')
parser.set_defaults(timing=False)
parser.add_argument('--getNIter', dest='getNIter', action='store_true')
parser.add_argument('--no-getNIter', dest='getNIter', action='store_false')
parser.set_defaults(getNIter=False)
parser.add_argument('--getELBO', dest='getELBO', action='store_true')
parser.add_argument('--no-getELBO', dest='getELBO', action='store_false')
parser.set_defaults(getELBO=False)
parser.add_argument('--debug', dest='debug', action='store_true')
parser.add_argument('--no-debug', dest='debug', action='store_false')
parser.set_defaults(debug=True)
args = parser.parse_args()

N = args.nElements
MAX_ITERS = args.maxIter
DATA_MEAN = 7
THRESHOLD = 1e-6

sess = tf.Session()

# Data generation
xn = tf.convert_to_tensor(np.random.normal(DATA_MEAN, 1, N), dtype=tf.float64)

if args.timing:
    init_time = time()

# Model hyperparameters
m = tf.Variable(0., dtype=tf.float64)
beta = tf.Variable(0.0001, dtype=tf.float64)
a = tf.Variable(0.001, dtype=tf.float64)
b = tf.Variable(0.001, dtype=tf.float64)

# Needed for variational initilizations
a_gamma_ini = np.random.gamma(1, 1, 1)[0]
b_gamma_ini = np.random.gamma(1, 1, 1)[0]

# Variational parameters
a_gamma = tf.Variable(a_gamma_ini, dtype=tf.float64)
b_gamma = tf.Variable(b_gamma_ini, dtype=tf.float64)
m_mu = tf.Variable(np.random.normal(0., (0.0001) ** (-1.), 1)[0],
                   dtype=tf.float64)
beta_mu = tf.Variable(np.random.gamma(a_gamma_ini, b_gamma_ini, 1)[0],
                      dtype=tf.float64)

# Lower Bound definition
LB = tf.mul(tf.cast(1. / 2, tf.float64), tf.log(tf.div(beta, beta_mu)))
LB = tf.add(LB, tf.mul(tf.mul(tf.cast(1. / 2, tf.float64),
                              tf.add(tf.pow(m_mu, 2),
                                     tf.div(tf.cast(1., tf.float64), beta_mu))),
                       tf.sub(beta_mu, beta)))
LB = tf.sub(LB, tf.mul(m_mu, tf.sub(tf.mul(beta_mu, m_mu), tf.mul(beta, m))))
LB = tf.add(LB, tf.mul(tf.cast(1. / 2, tf.float64),
                       tf.sub(tf.mul(beta_mu, tf.pow(m_mu, 2)),
                              tf.mul(beta, tf.pow(m, 2)))))

LB = tf.add(LB, tf.mul(a, tf.log(b)))
LB = tf.sub(LB, tf.mul(a_gamma, tf.log(b_gamma)))
LB = tf.add(LB, tf.lgamma(a_gamma))
LB = tf.sub(LB, tf.lgamma(a))
LB = tf.add(LB, tf.mul(tf.sub(tf.digamma(a_gamma), tf.log(b_gamma)),
                       tf.sub(a, a_gamma)))
LB = tf.add(LB, tf.mul(tf.div(a_gamma, b_gamma), tf.sub(b_gamma, b)))

LB = tf.add(LB, tf.mul(tf.div(tf.cast(N, tf.float64), tf.cast(2., tf.float64)),
                       tf.sub(tf.digamma(a_gamma), tf.log(b_gamma))))
LB = tf.sub(LB, tf.mul(tf.div(tf.cast(N, tf.float64), tf.cast(2., tf.float64)),
                       tf.log(tf.mul(tf.cast(2., tf.float64), math.pi))))
LB = tf.sub(LB, tf.mul(tf.cast(1. / 2, tf.float64),
                       tf.mul(tf.div(a_gamma, b_gamma),
                              tf.reduce_sum(tf.pow(xn, 2)))))
LB = tf.add(LB,
            tf.mul(tf.div(a_gamma, b_gamma), tf.mul(tf.reduce_sum(xn), m_mu)))
LB = tf.sub(LB, tf.mul(tf.div(tf.cast(N, tf.float64), tf.cast(2., tf.float64)),
                       tf.mul(tf.div(a_gamma, b_gamma), tf.add(tf.pow(m_mu, 2),
                                                               tf.div(
                                                                   tf.cast(1.,
                                                                           tf.float64),
                                                                   beta_mu)))))

# Parameter updates
assign_m_mu = m_mu.assign(tf.div(tf.add(tf.mul(beta, m),
                                        tf.mul(tf.div(a_gamma, b_gamma),
                                               tf.reduce_sum(xn))),
                                 tf.add(beta, tf.mul(tf.cast(N, tf.float64),
                                                     tf.div(a_gamma,
                                                            b_gamma)))))
assign_beta_mu = beta_mu.assign(
    tf.add(beta, tf.mul(tf.cast(N, tf.float64), tf.div(a_gamma, b_gamma))))
assign_a_gamma = a_gamma.assign(
    tf.add(a, tf.div(tf.cast(N, tf.float64), tf.cast(2., tf.float64))))
assign_b_gamma = b_gamma.assign(tf.add(b, tf.add(
    tf.sub(tf.mul(tf.cast(1. / 2, tf.float64), tf.reduce_sum(tf.pow(xn, 2))),
           tf.mul(m_mu, tf.reduce_sum(xn))),
    tf.mul(tf.div(tf.cast(N, tf.float64), tf.cast(2., tf.float64)),
           tf.add(tf.pow(m_mu, 2), tf.div(tf.cast(1., tf.float64), beta_mu))))))

# Summaries definition
tf.summary.histogram('m_mu', m_mu)
tf.summary.histogram('beta_mu', beta_mu)
tf.summary.histogram('a_gamma', a_gamma)
tf.summary.histogram('b_gamma', b_gamma)
merged = tf.summary.merge_all()
file_writer = tf.summary.FileWriter('/tmp/tensorboard/', tf.get_default_graph())


def main():
    init = tf.global_variables_initializer()
    sess.run(init)
    lbs = []
    run_calls = 0

    for i in xrange(MAX_ITERS):

        # Parameter updates
        sess.run([assign_m_mu, assign_beta_mu, assign_a_gamma])
        sess.run(assign_b_gamma)
        mu_out, beta_out, a_out, b_out = sess.run(
            [m_mu, beta_mu, a_gamma, b_gamma])

        # ELBO computation
        mer, lb = sess.run([merged, LB])
        if args.debug:
            print('Iter {}: Mu={} Precision={} ELBO={}'
                  .format(i, mu_out, a_out / b_out, lb))
        run_calls += 1
        file_writer.add_summary(mer, run_calls)

        # Break condition
        if i > 0:
            if abs(lb - lbs[i - 1]) < THRESHOLD:
                if args.getNIter:
                    n_iters = i + 1
                break
        lbs.append(lb)

    if args.timing:
        final_time = time()
        exec_time = final_time - init_time
        print('Time: {} seconds'.format(exec_time))

    if args.getNIter:
        print('Iterations: {}'.format(n_iters))

    if args.getELBO:
        print('ELBOs: {}'.format(lbs))


if __name__ == '__main__': main()