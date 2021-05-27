#--------------------------------------
# Colin.D.Mclean@ed.ac.uk (09/10/2018)
# Test the ontology service
# Using phython 3.7, i.e. > python3 HPOobo2NEO4J_v4.py
# EXAMPLES: The ontobio package will handle any ontoloy in the OLS (https://www.ebi.ac.uk/ols/ontologies), i.e
#            HP  = Human Pheontype Ontology
#           DOID = Human Disease Ontology
#           GO   = Gene Ontology
# We can also load 'local' ontologies from file, for example in the OBO .json graph format, i.e.
#   SIDB-network-service/test/data/local_ontologies/ASDPhenotypeOntology_Public.json (ASDPTO)
#   SIDB-network-service/test/data/local_ontologies/autism-merged.json               (ADAR)
#
#--------------------------------------

from network.ontology_service import ontology

ontology_obo_name = ['hp', 'go', 'doid', 'asdpto', 'adar']
ontology_ID       = ['HP', 'GO', 'DOID', 'ASDPTO', 'ADAR']
ontology_rels     = ['subClassOf']


def run_ontology_service(indx):
    print("test loading the %s ontology...\n" %(ontology_ID[indx]))
    on = ontology()
    on.load(name=ontology_obo_name[indx],
            pref=ontology_ID[indx],
            rels=ontology_rels[0])

    print(">> %s network: nodes %d, edges %d \n"
          % (ontology_ID[indx], on.gg.number_of_nodes(), on.gg.number_of_edges()))
    print("... done.\n")
    return on

def test_ontology_HP():
    on=run_ontology_service(0)
    # assert on.gg.number_of_nodes()==45009
    # assert on.gg.number_of_edges()==77185


def test_ontology_ASDPTO():
    on=run_ontology_service(3)
    # assert on.gg.number_of_nodes()==3070
    # assert on.gg.number_of_edges()==1852
