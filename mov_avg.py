import numpy as np
import matplotlib.pyplot as plt
modes = ['full', 'same', 'valid']

for n in range(1,10,1):
    rnd = np.random.rand(200)
    for m in modes:
        #plt.plot(rnd)
        plt.plot(np.convolve(rnd, np.random.rand(50)/50, mode=m));
    plt.axis([-10, 251, -.1, 1.1]);
    plt.legend(modes, loc='lower center');
    plt.show()

