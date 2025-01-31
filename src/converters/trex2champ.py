#!/usr/bin/env python3
#   trex2champ is a tool which allows to read output files of quantum
#   chemistry codes (GAMESS and trexio files) and write input files for
#   CHAMP in V2.0 format.
#
# Copyright (c) 2021, TREX Center of Excellence
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#   Ravindra Shinde
#   University of Twente
#   Enschede, The Netherlands
#   r.l.shinde@utwente.nl


__author__ = "Ravindra Shinde, Evgeny Posenitskiy"
__copyright__ = "Copyright 2021, The TREX Project"
__version__ = "1.0.0"
__maintainer__ = "Ravindra Shinde"
__email__ = "r.l.shinde@utwente.nl"
__status__ = "Development"


from operator import index
import sys
import os
import numpy as np
from collections import Counter


try:
    import trexio
except:
    print("Error: The TREXIO Python library is not installed")
    sys.exit(1)

try:
    import resultsFile
except:
    print("Error: The resultsFile Python library is not installed")
    sys.exit(1)

def run(filename,  gamessfile, back_end, motype=None):

    trexio_file = trexio.File(filename, mode='r',back_end=back_end)


    # Metadata
    # --------

    metadata_num = trexio.read_metadata_code_num(trexio_file)
    metadata_code  = trexio.read_metadata_code(trexio_file)
    metadata_description = trexio.read_metadata_description(trexio_file)

    # Electrons
    # ---------

    electron_up_num = trexio.read_electron_up_num(trexio_file)
    electron_dn_num = trexio.read_electron_dn_num(trexio_file)

    # Nuclei
    # ------

    nucleus_num = trexio.read_nucleus_num(trexio_file)
    nucleus_charge = trexio.read_nucleus_charge(trexio_file)
    nucleus_coord = trexio.read_nucleus_coord(trexio_file)
    nucleus_label = trexio.read_nucleus_label(trexio_file)
    nucleus_point_group = trexio.read_nucleus_point_group(trexio_file)


    # ECP
    # ------

    ecp_num = trexio.read_ecp_num(trexio_file)
    ecp_z_core = trexio.read_ecp_z_core(trexio_file)
    ecp_max_ang_mom_plus_1 = trexio.read_ecp_max_ang_mom_plus_1(trexio_file)
    ecp_ang_mom = trexio.read_ecp_ang_mom(trexio_file)
    ecp_nucleus_index = trexio.read_ecp_nucleus_index(trexio_file)
    ecp_exponent = trexio.read_ecp_exponent(trexio_file)
    ecp_coefficient = trexio.read_ecp_coefficient(trexio_file)
    ecp_power = trexio.read_ecp_power(trexio_file)


    # Basis

    dict_basis = {}
    dict_basis["type"] = trexio.read_basis_type(trexio_file)
    dict_basis["shell_num"] = trexio.read_basis_shell_num(trexio_file)
    dict_basis["prim_num"] = trexio.read_basis_prim_num(trexio_file)
    dict_basis["nucleus_index"] = trexio.read_basis_nucleus_index(trexio_file)
    dict_basis["shell_ang_mom"] = trexio.read_basis_shell_ang_mom(trexio_file)
    dict_basis["shell_factor"] = trexio.read_basis_shell_factor(trexio_file)
    dict_basis["shell_index"] = trexio.read_basis_shell_index(trexio_file)
    dict_basis["exponent"] = trexio.read_basis_exponent(trexio_file)
    dict_basis["coefficient"] = trexio.read_basis_coefficient(trexio_file)
    dict_basis["prim_factor"] = trexio.read_basis_prim_factor(trexio_file)

    # AO
    # --

    ao_cartesian = trexio.read_ao_cartesian(trexio_file)
    ao_num = trexio.read_ao_num(trexio_file)
    ao_shell = trexio.read_ao_shell(trexio_file)
    ao_normalization = trexio.read_ao_normalization(trexio_file)


    # MOs
    # ---
    dict_mo = {}
    dict_mo["type"] = trexio.read_mo_type(trexio_file)
    dict_mo["num"] = trexio.read_mo_num(trexio_file)
    dict_mo["coefficient"] = trexio.read_mo_coefficient(trexio_file)
    dict_mo["symmetry"] = trexio.read_mo_symmetry(trexio_file)




    ###### NOTE ######
    # The following portion is written to convert the data available in the
    # TREXIO file to the format readable by CHAMP.
    # Note all the information is yet not available in trexio file.
    # The determinants and csf information is obtained from the GAMESS output file using the resultsFile package.
    # It will be replaced by the data stored by trexio later in the future.

    # Write the .xyz file containing cartesian coordinates (Bohr) of nuclei
    write_champ_file_geometry(filename, nucleus_num, nucleus_label, nucleus_coord)

    # Write the ECP files for each unique atoms
    write_champ_file_ecp_trexio(filename, nucleus_num, nucleus_label, ecp_num, ecp_z_core, ecp_max_ang_mom_plus_1, ecp_ang_mom, ecp_nucleus_index, ecp_exponent, ecp_coefficient, ecp_power)

    # Write the .sym file containing symmetry information of MOs
    write_champ_file_symmetry(filename, dict_mo)

    # Write the .lcao and .bfinfo file containing orbital information of MOs
    write_champ_file_orbitals(filename, dict_basis, dict_mo, ao_num, nucleus_label)

    # Write the basis on the radial grid file
    write_champ_file_basis_grid(filename, dict_basis, nucleus_label)

    # Write the determinants, csf and csfmap into a single file using the resultsFile package
    file = resultsFile.getFile(gamessfile)
    write_champ_file_determinants(filename, file)

    # Write the eigenvalues for a given type of orbitals using the resultsFile package. Currently it is optional.
    # write_champ_file_eigenvalues(filename, file, dict_mo["type"])

    return



## Champ v2.0 format input files

# Radial basis on the grid
def write_champ_file_basis_grid(filename, dict_basis, nucleus_label):
    """Writes the radial basis data onto a grid for champ calculation.

    Returns:
        None
    """
    gridtype=3
    gridpoints=2000
    gridarg=1.003
    gridr0=20.0
    gridr0_save = gridr0

    # Get the number of shells per atom
    list_shell, list_nshells = np.unique(dict_basis["nucleus_index"], return_counts=True)

    contr = [ { "exponent"      : [],
                "coefficient"   : [],
                "prim_factor"   : []  }  for _ in range(dict_basis["shell_num"]) ]
    for j in range(dict_basis["prim_num"]):
        i = dict_basis["shell_index"][j]
        contr[i]["exponent"]    += [ dict_basis["exponent"][j] ]
        contr[i]["coefficient"] += [ dict_basis["coefficient"][j] ]
        contr[i]["prim_factor"] += [ dict_basis["prim_factor"][j] ]

    basis = {}
    for k in range(len(nucleus_label)):
        basis[k] = { "shell_ang_mom" : [],
                    "shell_factor"  : [],
                    "shell_index"   : [],
                    "contr"         : [] }

    for i in range(dict_basis["shell_num"]):
        k = dict_basis["nucleus_index"][i]
        basis[k]["shell_ang_mom"] += [ dict_basis["shell_ang_mom"][i] ]
        basis[k]["shell_factor"]  += [ dict_basis["shell_factor"][i] ]
        basis[k]["shell_index"]   += [ dict_basis["shell_index"][i] ]
        basis[k]["contr"]         += [ contr[i] ]

    # Get the index array of the primitives for each atom
    index_primitive = []; counter = 0;
    index_primitive.append(0) # The starting index of the first primitive of the first atom
    for nucleus in range(len(nucleus_label)):
        for l in range(len(basis[nucleus]["shell_index"])):
            ncontr = len(basis[nucleus]["contr"][l]["exponent"])
            counter += ncontr
            if l == 0 and nucleus > 0:
                index_primitive.append(counter)

    # Get the index array of the shells for each atom
    index_radial = [[] for i in range(len(nucleus_label))]; counter = 0
    for i in range(len(nucleus_label)):
        for ind, val in enumerate(dict_basis["nucleus_index"]):
            if val == i:
                index_radial[i].append(counter)
                counter += 1


    # Gaussian normalization
    def gnorm(alp,l):
        norm = 1.0          # default normalization
        if l == 0:
            norm = (2.0*alp)**(3.0/4.0)*2.0*(1.0/(np.pi**(1.0/4.0)))
        elif l == 1:
            norm = (2.0*alp)**(5.0/4.0)*np.sqrt(8.0/3.0)*(1.0/(np.pi**(1.0/4.0)))
        elif l == 2:
            norm = (2.0*alp)**(7.0/4.0)*np.sqrt(16.0/15.0)*(1.0/(np.pi**(1.0/4.0)))
        elif l == 3:
            norm = (2.0*alp)**(9.0/4.0)*np.sqrt(32.0/105.0)*(1.0/(np.pi**(1.0/4.0)))
        return norm

    def compute_grid():
        # Compute the radial grid r for a given number of grid points
        # and grid type
        for i in range(gridpoints):
            if gridtype == 1:
                r = gridr0 + i*gridarg
            elif gridtype == 2:
                r = gridr0 * gridarg**i
            elif gridtype == 3:
                r = gridr0 * gridarg**i - gridr0
            bgrid[:,i] = r
        return bgrid

    def add_function(shell_ang_mom, exponents, coefficients, shell, bgrid):
        # put a new function on the grid
        # The function is defined by the exponent, coefficient and type
        for i in range(gridpoints):
            r = bgrid[shell+1, i]
            r2 = r*r
            r3 = r2*r
            value = 0.0
            for j in range(len(exponents)):
                value += gnorm(exponents[j], shell_ang_mom) * coefficients[j] * np.exp(-exponents[j]*r2)
                # print ("each value k, ib,", i ,j , value)
            if shell_ang_mom == 1:
                value *= r
            elif shell_ang_mom == 2:
                value *= r2
            elif shell_ang_mom == 3:
                value *= r3

            bgrid[shell+1,i] = value

        return

    if filename is not None:
        if isinstance(filename, str):
            unique_elements, indices = np.unique(nucleus_label, return_index=True)

            for i in range(len(unique_elements)):
                # Write down an radial basis grid file in the new champ v2.0 format for each unique atom type
                filename_basis_grid = "BFD-Q." + 'basis.' + unique_elements[i]
                with open(filename_basis_grid, 'w') as file:

                    # Common numbers
                    gridtype=3
                    gridpoints=2000
                    gridarg=1.003
                    gridr0=20.0

                    number_of_shells_per_atom = list_nshells[indices[i]]

                    shell_ang_mom_per_atom_list = []
                    for ind, val in enumerate(dict_basis["nucleus_index"]):
                        if val == indices[i]:
                            shell_ang_mom_per_atom_list.append(dict_basis["shell_ang_mom"][ind])

                    shell_ang_mom_per_atom_count = Counter(shell_ang_mom_per_atom_list)

                    total_shells = sum(shell_ang_mom_per_atom_count.values())

                    shells_per_atom = {}
                    for count in shell_ang_mom_per_atom_count:
                        shells_per_atom[count] = shell_ang_mom_per_atom_count[count]

                    bgrid = np.zeros((number_of_shells_per_atom+1, gridpoints))


                    ## The main part of the file starts here
                    gridr0_save = gridr0
                    if gridtype == 3:
                        gridr0 = gridr0/(gridarg**(gridpoints-1)-1)


                    bgrid = compute_grid()  # Compute the grid, store the results in bgrid

                    ### Note temp index should point to shell index of unique atoms
                    # get the exponents and coefficients of unique atom types
                    counter = 0
                    for ind, val in enumerate(dict_basis["nucleus_index"]):
                        if val == indices[i]:
                            shell_index_unique_atom = index_radial[indices[i]][counter]
                            list_contracted_exponents =  contr[shell_index_unique_atom]["exponent"]
                            list_contracted_coefficients =  contr[shell_index_unique_atom]["coefficient"]
                            add_function(dict_basis["shell_ang_mom"][ind], list_contracted_exponents, list_contracted_coefficients, counter, bgrid)
                            counter += 1


                    # file writing part
                    file.write(f"{number_of_shells_per_atom} {gridtype} {gridpoints} {gridarg:0.6f} {gridr0_save:0.6f} {0}\n")
                    np.savetxt(file, np.transpose(bgrid), fmt=' %.12e')

                file.close()
        else:
            raise ValueError
    # If filename is None, return a string representation of the output.
    else:
        return None


def write_champ_file_determinants(filename, file):
    """Writes the determinant data from the quantum
    chemistry calculation to a champ v2.0 format file.

    Returns:
        None as a function value
    """
    import copy
    det_coeff = file.det_coefficients
    csf_coeff = file.csf_coefficients

    num_csf = len(csf_coeff[0])
    num_states = file.num_states
    num_dets = len(det_coeff[0])
    num_alpha = len(file.determinants[0].get("alpha"))
    num_beta = len(file.determinants[0].get("beta"))

    alpha_orbitals = np.sort(file.determinants[0].get("alpha"))
    beta_orbitals = np.sort(file.determinants[0].get("beta"))

    # Get the core+active space
    for det in range(len(det_coeff[0])): #reduced_list_determintants:
        alpha = file.determinants[det].get("alpha")
        beta = file.determinants[det].get("beta")
        maxalpha = max(alpha); maxbeta = max(beta)

    qmc_phase_factor = []
    for det in range(len(det_coeff[0])): #reduced_list_determintants:
        alpha = file.determinants[det].get("alpha")
        beta = file.determinants[det].get("beta")

        alpha_occup = np.zeros(maxalpha+1,dtype=str)
        beta_occup  = np.zeros(maxbeta+1,dtype=str)

        for a in alpha:
            alpha_occup[a] = "a"
        for b in beta:
            beta_occup[b]  = "b"

        occupation = [x[0]+x[1] for x in zip(alpha_occup, beta_occup)]

        phase_count = 0

        for j in range(len(occupation)):
            if occupation[j] == "b" or occupation[j] == "ab":
                for k in range(j+1,len(occupation)):
                    if occupation[k] == "a" or occupation[k] == "ab":
                        phase_count += 1
        qmc_phase_factor.append((-1)**phase_count)

    temp_counter = 0; flat_array_coeff=[]
    for i in range(len(file._csf)):
        for ind, coeff in enumerate(file._csf[i].coefficients):
            file._csf[i].coefficients[ind] = file._csf[i].coefficients[ind]*qmc_phase_factor[temp_counter]
            flat_array_coeff.append(file._csf[i].coefficients[ind])
            temp_counter += 1

    ## Do the preprocessing to reduce the number of determinants and get the CSF mapping
    reduced_det_coefficients = []
    csf = file.csf
    reduced_list_determintants = []
    copy_list_determintants = []

    ## Get which determinant coefficient correspond to which csf coefficient
    csf_for_each_det = []
    for state_coef in file.csf_coefficients:
        for i,c in enumerate(state_coef):
            for d in csf[i].coefficients:
                csf_for_each_det.append(c)

    # Get the reduced determinant coefficients
    for state_coef in file.csf_coefficients:
        vector = []
        counter = 0; counter2 = 0       # Counter2 is required for keeping correspondence of determinants in the reduced list
        for i,c in enumerate(state_coef):
            for d in csf[i].coefficients:
                temp = 0.0
                indices = [i for i, x in enumerate(file.determinants) if x == file.determinants[counter]]
                if counter == indices[0]:
                    copy_list_determintants.append(counter2)
                    counter2 += 1
                    reduced_list_determintants.append(indices[0])
                    for index in indices:
                        if len(indices) == 1:
                            temp =  csf_for_each_det[index] * flat_array_coeff[index]
                        else:
                            temp += csf_for_each_det[index] * flat_array_coeff[index]
                    vector.append(temp)
                else:
                    copy_list_determintants.append(indices[0])
                counter += 1
        reduced_det_coefficients.append(vector)


    if filename is not None:
        if isinstance(filename, str):
            ## Write down a determinant file in the new champ v2.0 format
            filename_determinant = os.path.splitext("champ_v2_" + filename)[0]+'_determinants.det'
            with open(filename_determinant, 'w') as f:
                # header line printed below
                f.write("# Determinants, CSF, and CSF mapping from the GAMESS output / TREXIO file. \n")
                f.write("# Converted from the trexio file using trex2champ converter https://github.com/TREX-CoE/trexio_tools \n")
                f.write("determinants {} {} \n".format(len(reduced_list_determintants), num_states))

                # print the determinant coefficients
                for state in range(num_states):
                    for det in range(len(reduced_list_determintants)):
                        f.write("{:.8f} ".format(reduced_det_coefficients[state][det]))
                    f.write("\n")

                # print the determinant orbital mapping
                for det in reduced_list_determintants:
                    for num in range(num_alpha):
                        alpha_orbitals = np.sort(file.determinants[det].get("alpha"))[num]+1
                        f.write("{:4d} ".format(alpha_orbitals))
                    f.write("  ")
                    for num in range(num_beta):
                        beta_orbitals = np.sort(file.determinants[det].get("beta"))[num]+1
                        f.write("{:4d} ".format(beta_orbitals))
                    f.write("\n")
                f.write("end \n")

                # print the CSF coefficients
                f.write("csf {} {} \n".format(num_csf, num_states))
                for state in range(num_states):
                    for ccsf in range(num_csf):
                        f.write("{:.8f} ".format(csf_coeff[state][ccsf]))
                    f.write("\n")
                f.write("end \n")

                # print the CSFMAP information
                f.write("csfmap \n")
                f.write("{} {} {} \n".format(num_csf,  len(reduced_list_determintants), num_dets))

                determinants_per_csf = []
                csf_det_coeff = []
                for state_coef in file.csf_coefficients:
                    for i,c in enumerate(state_coef):
                        determinants_per_csf.append(len(csf[i].coefficients))
                        for d in csf[i].coefficients:
                            csf_det_coeff.append(d)


                for state in range(num_states):
                    i = 0
                    for csf in range(num_csf):
                        f.write(f"{determinants_per_csf[csf]:d} \n")
                        for num in range(determinants_per_csf[csf]):
                            f.write(f"  {copy_list_determintants[i]+1}  {csf_det_coeff[i]:.6f} \n")
                            i += 1
                f.write("end \n")

                f.write("\n")
            f.close()
        else:
            raise ValueError
    # If filename is None, return a string representation of the output.
    else:
        return None




# Geometry
def write_champ_file_geometry(filename, nucleus_num, nucleus_label, nucleus_coord):
    """Writes the geometry data from the quantum
    chemistry calculation to a champ v2.0 format file.

    Returns:
        None as a function value
    """

    if filename is not None:
        if isinstance(filename, str):
            ## Write down a geometry file in the new champ v2.0 format
            filename_geometry = os.path.splitext("champ_v2_" + filename)[0]+'_geom.xyz'
            with open(filename_geometry, 'w') as file:

                file.write("{} \n".format(nucleus_num))
                # header line printed below
                file.write("# Converted from the trexio file using trex2champ converter https://github.com/TREX-CoE/trexio_tools \n")

                for element in range(nucleus_num):
                   file.write("{:5s} {: 0.6f} {: 0.6f} {: 0.6f} \n".format(nucleus_label[element], nucleus_coord[element][0], nucleus_coord[element][1], nucleus_coord[element][2]))

                file.write("\n")
            file.close()
        else:
            raise ValueError
    # If filename is None, return a string representation of the output.
    else:
        return None

# Symmetry
def write_champ_file_symmetry(filename, dict_mo):
    """Writes the symmetry information of molecular orbitals from the quantum
    chemistry calculation to the new champ v2.0 input file format.

    Returns:
        None as a function value
    """

    if filename is not None:
        if isinstance(filename, str):
            ## Write down a symmetry file in the new champ v2.0 format
            filename_symmetry = os.path.splitext("champ_v2_" + filename)[0]+'_symmetry.sym'
            with open(filename_symmetry, 'w') as file:

                values, counts = np.unique(dict_mo["symmetry"], return_counts=True)
                # point group symmetry independent line printed below
                file.write("sym_labels " + str(len(counts)) + " " + str(dict_mo["num"])+"\n")

                irrep_string = ""
                irrep_correspondence = {}
                for i, val in enumerate(values):
                    irrep_correspondence[val] = i+1
                    irrep_string += " " + str(i+1) + " " + str(val)

                if all(irreps in dict_mo["symmetry"] for irreps in values):
                    file.write(f"{irrep_string} \n")   # This defines the rule

                    for item in dict_mo["symmetry"]:
                        for key, val in irrep_correspondence.items():
                            if item == key:
                                file.write(str(val)+" ")
                    file.write("\n")
                file.write("end\n")
            file.close()

        else:
            raise ValueError
    # If filename is None, return a string representation of the output.
    else:
        return None


# eigenvalues
def write_champ_file_eigenvalues(filename, file, mo_type):
    """Writes the eigenvalue information of molecular orbitals from the quantum
    chemistry calculation to the new champ v2.0 input file format.

    Returns:
        None as a function value
    """

    # mo_type could be "GUGA", "Initial", "Natural", "CASSCF", "CASCI", "CASSCF_Natural"

    resultsfile_molecular_orbitals = file.mo_sets[mo_type]
    num_mo = len(resultsfile_molecular_orbitals)

    eigenvalues = [resultsfile_molecular_orbitals[i].eigenvalue for i in range(num_mo)]

    if filename is not None:
        if isinstance(filename, str):
            ## Write down a eigenvalues file in the new champ v2.0 format
            filename_eigenvalue = os.path.splitext("champ_v2_" + filename)[0]+'_eigenvalues.eig'
            with open(filename_eigenvalue, 'w') as file:

                # Write the header line
                file.write("# File created using the trex2champ converter https://github.com/TREX-CoE/trexio_tools  \n")
                file.write(f"# Eigenvalues correspond to the {mo_type} orbitals  \n")
                file.write("eigenvalues " + str(num_mo) + "\n")

                # Write the eigenvalues in one line
                for i in range(num_mo):
                    file.write(f"{eigenvalues[i]:0.4f} ")
                file.write("\n")
                file.write("end\n")
            file.close()

        else:
            raise ValueError
    # If filename is None, return a string representation of the output.
    else:
        return None


# Orbitals / LCAO infomation

def write_champ_file_orbitals(filename, dict_basis, dict_mo, ao_num, nucleus_label):
    """Writes the molecular orbitals coefficients from the quantum
    chemistry calculation / trexio file to champ v2.0 input file format.

    Returns:
        None as a function value
    """

    ## Cartesian Ordering CHAMP
    # basis_order = ['S',[all 'X'],[all 'Y'],[all 'Z'],'XX','XY','XZ','YY','YZ','ZZ','XXX','XXY','XXZ','XYY','XYZ','XZZ','YYY','YYZ','YZZ','ZZZ']
    # sequence of flags in qmc input
    label_ang_mom = {0:'S', 1:'P', 2:'D', 3:'F', 4:'G', 5:'H'}

    shells = {}
    shells[0] = ['S']
    shells[1] = ['X','Y','Z']
    shells[2] = ['XX','XY','XZ','YY','YZ','ZZ']
    shells[3] = ['XXX','XXY','XXZ','XYY','XYZ','XZZ','YYY','YYZ','YZZ','ZZZ']

    contr = [ { "exponent"      : [],
                "coefficient"   : [],
                "prim_factor"   : []  }  for _ in range(dict_basis["shell_num"]) ]
    for j in range(dict_basis["prim_num"]):
        i = dict_basis["shell_index"][j]
        contr[i]["exponent"]    += [ dict_basis["exponent"][j] ]
        contr[i]["coefficient"] += [ dict_basis["coefficient"][j] ]
        contr[i]["prim_factor"] += [ dict_basis["prim_factor"][j] ]

    basis = {}
    for k in range(len(nucleus_label)):
        basis[k] = { "shell_ang_mom" : [],
                    "shell_factor"  : [],
                    "shell_index"   : [],
                    "contr"         : [] }

    for i in range(dict_basis["shell_num"]):
        k = dict_basis["nucleus_index"][i]
        basis[k]["shell_ang_mom"] += [ dict_basis["shell_ang_mom"][i] ]
        basis[k]["shell_factor"]  += [ dict_basis["shell_factor"][i] ]
        basis[k]["shell_index"]   += [ dict_basis["shell_index"][i] ]
        basis[k]["contr"]         += [ contr[i] ]

    # Get the index array of the primitives for each atom
    index_primitive = []; counter = 0
    index_primitive.append(0) # The starting index of the first primitive of the first atom
    for nucleus in range(len(nucleus_label)):
        for l in range(len(basis[nucleus]["shell_index"])):
            ncontr = len(basis[nucleus]["contr"][l]["exponent"])
            counter += ncontr
            if l == 0 and nucleus > 0:
                index_primitive.append(counter)

    # Get the index array of the shells for each atom
    index_radial = [[] for i in range(len(nucleus_label))]; counter = 0
    for i in range(len(nucleus_label)):
        for ind, val in enumerate(dict_basis["nucleus_index"]):
            if val == i:
                index_radial[i].append(counter)
                counter += 1

    mo_num = dict_mo["num"]
    cartesian = True
    if cartesian:
        order = [ [0],
                [0, 1, 2],
                [0, 1, 2, 3, 4, 5],
                [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] ]
    else:
        print ("Orbitals in spherical representation detected")
        sys.exit()



#   Count how many times p,d,f appears for a given atom
    dict_sshell_count = {}; dict_pshell_count = {}; dict_dshell_count = {}; dict_fshell_count = {}
    for atom_index in range(len(index_radial)):
        counter_s = 0; counter_p = 0; counter_d = 0; counter_f = 0
        for i in index_radial[atom_index]:
            l = dict_basis["shell_ang_mom"][i]
            if l == 0:
                counter_s += 1
            if l == 1:
                counter_p += 1
            if l == 2:
                counter_d += 1
            if l == 3:
                counter_f += 1
        dict_sshell_count[atom_index] = counter_s
        dict_pshell_count[atom_index] = counter_p
        dict_dshell_count[atom_index] = counter_d
        dict_fshell_count[atom_index] = counter_f


    # print ("index radial: ", index_radial)
    # print ("dict basis: ", dict_basis["shell_ang_mom"])
    # print ("dict_sshell count: ", dict_sshell_count)
    # print ("dict_pshell count: ", dict_pshell_count)
    # print ("dict_dshell count: ", dict_dshell_count)
    # print ("dict_fshell count: ", dict_fshell_count)

    # This part is for reshuffling to make the AO basis in the CHAMP's own ordering
    index_dict = {}; shell_representation = {}; bf_representation = {}
    new_shell_representation = []
    counter = 0; basis_per_atom = []
    ind = 0; champ_ao_ordering = []
    for atom_index in range(len(index_radial)):
        bfcounter = 1; basis_per_atom_counter = 0
        pindex = 0; dindex = 0; findex = 0
        for i in index_radial[atom_index]:
            l = dict_basis["shell_ang_mom"][i]
            # run a small loop to reshuffle the shell ordering
            if l == 0:
                new_shell_representation.append(shells[l][0])
                champ_ao_ordering.append(ind)
                ind += 1

            local_p = np.zeros((3,dict_pshell_count[atom_index]),dtype='U1')
            local_ind_p = np.zeros((3,dict_pshell_count[atom_index]),dtype=int)
            if l == 1:
                pindex += 1; ind = champ_ao_ordering[-1] + 1
                for j in range(dict_pshell_count[atom_index]):
                    #loop over all 3 p orbitals
                    for k in order[l]:
                        local_p[k,j] = shells[l][k]
                        local_ind_p[k,j] = ind
                        ind += 1

                if pindex == dict_pshell_count[atom_index]:
                    new_shell_representation.extend(list(local_p.flatten()))
                    champ_ao_ordering.extend(list(local_ind_p.flatten()))



            local_d = np.zeros((6,dict_dshell_count[atom_index]),dtype='U2')
            local_ind_d = np.zeros((6,dict_dshell_count[atom_index]),dtype=int)
            if l == 2:
                dindex += 1; ind = champ_ao_ordering[-1] + 1
                for j in range(dict_dshell_count[atom_index]):
                    #loop over all 6 d orbitals
                    for k in order[l]:
                        local_d[k,j] = shells[l][k]
                        local_ind_d[k,j] = ind
                        ind += 1

                if dindex == dict_dshell_count[atom_index]:
                    new_shell_representation.extend(list(local_d.flatten()))
                    champ_ao_ordering.extend(list(local_ind_d.flatten()))


            local_f = np.zeros((10,dict_fshell_count[atom_index]),dtype='U3')
            local_ind_f = np.zeros((10,dict_fshell_count[atom_index]),dtype=int)
            if l == 3:
                findex += 1; ind = champ_ao_ordering[-1] + 1
                for j in range(dict_fshell_count[atom_index]):
                    #loop over all 10 f orbitals
                    for k in order[l]:
                        local_f[k,j] = shells[l][k]
                        local_ind_f[k,j] = ind
                        ind += 1

                if findex == dict_fshell_count[atom_index]:
                    new_shell_representation.extend(list(local_f.flatten()))
                    champ_ao_ordering.extend(list(local_ind_f.flatten()))

            # Get number of AO basis per atom
            for k in order[l]:
                shell_representation[counter] = shells[l][k]
                index_dict[counter] =  counter
                bf_representation[counter] = bfcounter
                counter += 1
                basis_per_atom_counter += 1
            bfcounter += 1
        basis_per_atom.append(basis_per_atom_counter)

    # print ("champ ao ordering: ", champ_ao_ordering)
    # print ("new_shell_representation: ", new_shell_representation)
    # print ("old_shell_representation: ", shell_representation.values())
    # print ("basis per atom: ", basis_per_atom)
    # print ("BF representation: ", bf_representation.values())


    ## Reorder orbitals according to the ordering of the CHAMP ordering
    reordered_mo_array = dict_mo["coefficient"][:,champ_ao_ordering]


    # The next two arrays are needed for bfinfo file
    reordered_bf_array = {k: bf_representation[k] for k in champ_ao_ordering}
    reordered_bf_array_values = list(reordered_bf_array.values())
    shell_representation_values = list(shell_representation.values())

    # print( "bf   ", reordered_bf_array_values)

    accumumulated_basis_per_atom = np.cumsum(basis_per_atom)

    start_index = 0
    basis_pointer_per_atom = []
    shell_reprensentation_per_atom = []
    for i in range(len(basis_per_atom)):
        end_index = accumumulated_basis_per_atom[i]
        basis_pointer_per_atom.append(reordered_bf_array_values[start_index:end_index])
        shell_reprensentation_per_atom.append(shell_representation_values[start_index:end_index])
        start_index = end_index



    ## write the information to the bfinfo file
    # Get the indices of unique atoms
    unique_atoms, unique_atom_indices = np.unique(nucleus_label, return_index=True)
    if filename is not None:
        if isinstance(filename, str):
            ## Write down a symmetry file in the new champ v2.0 format
            filename_bfinfo = os.path.splitext("champ_v2_" + filename)[0]+'.bfinfo'
            with open(filename_bfinfo, 'w') as file:

                # qmc bfinfo line printed below
                file.write("qmc_bf_info 1 \n")

                # pointers to the basis functions
                for i in unique_atom_indices:
                    count_shells_per_atom = list(Counter(shell_reprensentation_per_atom[i]).values())
                    # Write the number of types of shells for each unique atom
                    for num in count_shells_per_atom:
                        file.write(f"{num} ")
                    # Write down zeros for shells that are not present. Total shells supported are S(1) + P(3) + D(6) + F(10) = 20
                    for rem in range(len(count_shells_per_atom), 20):
                        file.write(f"0 ")
                    file.write(f"\n")

                    # Write the pointers to the basis functions
                    for pointer in basis_pointer_per_atom[i]:
                        file.write(f"{pointer} ")
                    file.write(f"\n")
                file.write("end\n")
            file.close()

        else:
            raise ValueError
    # If filename is None, return a string representation of the output.
    else:
        return None
    # all the bfinfo file information written to the file

    # write the molecular coefficients to the .lcao file
    if filename is not None:
        if isinstance(filename, str):
            ## Write down an orbitals file in the new champ v2.0 format
            filename_orbitals = os.path.splitext("champ_v2_" + filename)[0]+'_orbitals.lcao'
            with open(filename_orbitals, 'w') as file:

                # header line printed below
                file.write("# File created using the trex2champ converter https://github.com/TREX-CoE/trexio_tools  \n")
                file.write("lcao " + str(dict_mo["num"]) + " " + str(ao_num) + " 1 " + "\n" )
                np.savetxt(file, reordered_mo_array, fmt='%.8f')
                file.write("end\n")
            file.close()
        else:
            raise ValueError
    # If filename is None, return a string representation of the output.
    else:
        return None
    # all the lcao file information written to the file


# ECP / Pseudopotential files using the trexio file
def write_champ_file_ecp_trexio(filename, nucleus_num, nucleus_label, ecp_num, ecp_z_core, ecp_max_ang_mom_plus_1, ecp_ang_mom, ecp_nucleus_index, ecp_exponent, ecp_coefficient, ecp_power):
    """Writes the Gaussian - effective core potential / pseudopotential data from
    the quantum chemistry calculation to a champ v2.0 format file.

    Returns:
        None as a function value
    """

    if filename is not None:
        if isinstance(filename, str):
            unique_elements, indices = np.unique(nucleus_label, return_index=True)
            for i in range(len(unique_elements)):
                # Write down an ECP file in the new champ v2.0 format for each nucleus
                filename_ecp = "BFD." + 'gauss_ecp.dat.' + unique_elements[i]
                with open(filename_ecp, 'w') as file:
                    file.write("BFD {:s} pseudo \n".format(unique_elements[i]))

                    dict_ecp={}
                    # get the indices of the ecp data for each atom
                    for ind, val in enumerate(ecp_nucleus_index):
                        if val == indices[i]:
                            dict_ecp[ind] = [ecp_ang_mom[ind], ecp_coefficient[ind], ecp_power[ind]+2, ecp_exponent[ind]]

                    ecp_array =  np.array(list(dict_ecp.values()))
                    ecp_array = ecp_array[np.argsort(ecp_array[:,0])]

                    sorted_list = np.sort(ecp_array[:,0])[::-1]

                    np.savetxt(file, [len(np.unique(sorted_list))], fmt='%d')
                    # loop over ang mom for a given atom
                    for l in np.sort(np.unique(sorted_list))[::-1]:
                        # loop and if condition to choose the correct components
                        for x in np.unique(np.sort(ecp_array[:,0])[::-1]):
                            if ecp_array[int(x):,0:][0][0] == l:
                                count = np.count_nonzero(sorted_list == l)
                                np.savetxt(file, [count], fmt='%d')
                                np.savetxt(file, ecp_array[int(x):count+int(x),1:], fmt='%.8f')

                file.close()

        else:
            raise ValueError
    # If filename is None, return a string representation of the output.
    else:
        return None