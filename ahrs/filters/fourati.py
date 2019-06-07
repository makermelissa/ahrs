# -*- coding: utf-8 -*-
"""
Fourati Fiter Algorithm as proposed by Hassen Fourati et al [1]_.

Based on the implementation by T. Michel for his project "On Attitude Estimation
with Smartphones" (http://tyrex.inria.fr/mobile/benchmarks-attitude).

References
----------
.. [1] Hassen Fourati, Noureddine Manamanni, Lissan Afilal, Yves Handrich. A
   Nonlinear Filtering Approach for the Attitude and Dynamic Body Acceleration
   Estimation Based on Inertial and MagneticSensors: Bio-Logging Application.
   IEEE Sensors Journal, Institute of Electrical and Electronics Engineers,
   2011, 11 (1), pp. 233-244. 10.1109/JSEN.2010.2053353. hal-00624142
   (https://hal.archives-ouvertes.fr/hal-00624142/file/Papier_IEEE_Sensors_Journal.pdf)

"""

import numpy as np
from ahrs.common.orientation import *
from ahrs.common.mathfuncs import *

class Fourati:
    """
    Fourati filter algorithm

    Parameters
    ----------
    k : float
        Filter gain for convergence
    ka : float
        Filter gain of the accelerometers.
    km : float
        Filter gain of the magnetometers.
    samplePeriod : float
        Sampling rate in seconds. Inverse of sampling frequency.

    """
    def __init__(self, *args, **kwargs):
        self.k = kwargs.get('k', 0.3)
        self.ka = kwargs.get('ka', 2.0)
        self.km = kwargs.get('km', 1.0)
        self.samplePeriod = kwargs.get('samplePeriod', 1.0/256.0)
        # self.gravity = kwargs.get('gravity', 9.87)
        # Vector Representation of references measurements
        self.aq = np.array([0., 0., 1.0])
        self.mq = np.array([0.5*cosd(65.0), 0., 0.5*sind(65.0)]) # Using UK's magnetic reference
        self.mq /= np.linalg.norm(self.mq)

    def update(self, g, a, m, q):
        """
        Fourati's AHRS algorithm with a MARG architecture.

        Adapted to Python from original implementation by T. Michel.

        Parameters
        ----------
        g : array
            Sample of tri-axial Gyroscope in radians.
        a : array
            Sample of tri-axial Accelerometer.
        q : array
            A-priori quaternion.

        Returns
        -------
        q : array
            Estimated quaternion.

        """
        # handle NaNs
        a_norm = np.linalg.norm(a)
        if a_norm == 0:
            return q
        m_norm = np.linalg.norm(m)
        if m_norm == 0:
            return q
        # Normalize vectors
        a /= a_norm
        m /= m_norm
        q /= np.linalg.norm(q)
        # Levenberg Marquardt
        measurement = np.concatenate((a, m))
        estimation = np.concatenate((self.aq, self.mq))
        # Jacobian Matrix
        delta = 2.0*np.vstack((self.ka*skew(self.aq), self.km*skew(self.mq))).T
        # Gradient Descent correction
        d = 1.0e-5  # Guarantees a non-singular inverted term
        dq = (measurement-estimation)@(np.linalg.inv(delta@delta.T+d*np.identity(3))@delta).T
        qDot = 0.5*q_prod(q, np.concatenate(([0.0], g))) + self.k*q_prod(q, np.concatenate(([0.0], dq)))
        q += qDot*self.samplePeriod
        q /= np.linalg.norm(q)
        return q