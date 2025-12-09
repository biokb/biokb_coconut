from ast import Name

from rdflib.namespace import Namespace

BASE_URI = "https://biokb.scai.fraunhofer.de/coconut/"


COCONUT_BASE = Namespace("https://coconut.naturalproducts.net")

COMP_NS = Namespace(COCONUT_BASE + "/compound/coconut_id/")
REL_NS = Namespace(BASE_URI + "relation#")
NODE_NS = Namespace(BASE_URI + "node#")
INCHI_NS = Namespace("http://rdf.ncbi.nlm.nih.gov/pubchem/inchikey/")
CHEMICAL_CLASS_NS = Namespace(BASE_URI + "chemical_class/")
CHEMICAL_SUB_CLASS_NS = Namespace(BASE_URI + "chemical_sub_class/")
CHEMICAL_SUPER_CLASS_NS = Namespace(BASE_URI + "chemical_super_class/")
DIRECT_PARENT_CLASSIFICATION_NS = Namespace(BASE_URI + "direct_parent_classification/")
NP_CLASSIFIER_PATHWAY_NS = Namespace(BASE_URI + "np_classifier_pathway/")
NP_CLASSIFIER_SUPERCLASS_NS = Namespace(BASE_URI + "np_classifier_superclass/")
NP_CLASSIFIER_CLASS_NS = Namespace(BASE_URI + "np_classifier_class/")
WCVP_PLANT_NS = Namespace("https://biokb.scai.fraunhofer.de/wcvp/Plant#")
NCBI_TAXON_NS = Namespace("http://purl.obolibrary.org/obo/NCBITaxon_")
IPNI_NS = Namespace("https://ipni.org/n/")
