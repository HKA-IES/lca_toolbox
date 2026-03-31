# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import bw2io as bi
import bw2data as bd

# import your own module


"""
Run once to create the Brightway project "lca_toolbox_tests" to run the tests.
"""

if __name__ == "__main__":
    bd.projects.set_current("lca_toolbox_tests")
    if 'ecoinvent-3.12-cutoff' in bd.databases:
        print('ecoinvent 3.12 is already present in the project')
        # del bd.databases['ecoinvent-3.12-cutoff']
        # del bd.databases['ecoinvent-3.12-biosphere']
    else:
        bi.import_ecoinvent_release(
            version='3.12',
            system_model='cutoff',  # can be cutoff / apos / consequential / EN15804
        )
