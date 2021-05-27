# --------------------------------------
# Colin.D.Mclean@ed.ac.uk (09/10/2018)
# Test the patient_service class in src/
# Using phython 3, i.e. > python3 HPOobo2NEO4J_v4.py
# --------------------------------------


# --- python import statements
# Note to self.... only works once you've (built) installed the package
from network.patient_service import patient

def test_patient_service():

    pn = patient()
    pn.load_data()
    pn.get_nodes()
    pn.patientHPsim()
    pn.patientHPsim_edges()
    pn.get_edges()
    print("patient_network: nodes %d, edges %d"
          %(pn.gg.number_of_nodes(), pn.gg.number_of_edges()))

    assert pn.gg.number_of_nodes()==100
    assert pn.gg.number_of_edges()==288


def test_graph():
    from network.graphical_db_service import graphical_db
    gdb = graphical_db(graph=None)


