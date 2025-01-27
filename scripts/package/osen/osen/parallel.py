import os, sys
import time


def launch_parallel(prog, sim_init, sim_end, nbfork=5):

    os.system('export OMP_NUM_THREADS=1')

    list_simulation = range(sim_init, sim_end, 1)

    if (len(list_simulation) != 0):
        run_list = ["python " + prog + " " + str(ii) for ii in list_simulation]

    currentnbtask = 0

    for r in run_list:
        print(r)
        if currentnbtask == nbfork:
            os.wait()
        else:
            currentnbtask = currentnbtask + 1

        pid = os.fork()

        if pid == 0:
            os.system(r)
            sys.exit(0)

    for i in range(currentnbtask):
        os.wait()
