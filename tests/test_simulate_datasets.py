
#--- python import statements
# Note to self.... only works once you've (built) installed the package
from network.simulate_datasets import PatientDDD

def test_simulate_datasets():

    print("Starting test...")

    sim = PatientDDD()
    sim.load_data()
    sim.generate_dataset()
    sim.save_dataset()

    print("... done.\n")

