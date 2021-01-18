import cast_upgrade_1_6_5 # @UnusedImport
from cast.application import ApplicationLevelExtension, create_link,ReferenceFinder
import logging
from builtins import len


class CobolToIdeal(ApplicationLevelExtension):

    def end_application(self, application):
         
        ## Functionalities
        ## 1. Link calls from Cobol to Ideal
        ## 2. Link calls from Ideal to Cobol
        ## 3. Link calls from Ideal to PLI
        ## 4. Link calls from Ideal to ASM
        
        logging.info("Running code at the end of an application")
        cobol_unknown_list = []
        cobol_known_list = {}
        pli_main_list = {}
        asm_list = {}
        nbLinkCreated = 0
        ideal_program_list = []
        ideal_programs = {}
        links = []

        logging.info("****** Searching for CAST_COBOL_ProgramPrototype")
        #1.  for cobol_unknown in application.search_objects(['CAST_COBOL_ProgramPrototype']):
        for cobol_unknown in application.objects().has_type('CAST_COBOL_ProgramPrototype'):
            logging.info("Cobol CAST_COBOL_ProgramPrototype found: {}".format(cobol_unknown.get_name()))
            cobol_unknown_list.append(cobol_unknown)

        logging.info("****** Number of CAST_COBOL_ProgramPrototype {}".format(str(len(cobol_unknown_list))))
        
        logging.info("****** Searching for ideal_program")
        ideal_program_list = []
        for ideal_program in application.objects().has_type('ideal_program'):
            logging.info("IDEAL Programs found: {}".format(ideal_program.get_name()))
            ideal_program_list.append(ideal_program)
        logging.info("****** Number of CA IDEAL Programs {}".format(str(len(ideal_program_list))))
        
        logging.info("****** Creating Link between Unknown Cobol Program and Ideal Program")
        # matching by name : if CAST_COBOL_ProgramPrototype has same name as PLIMainProcedure, they are the same object
        for ideal_program in ideal_program_list:
            for cobol_unknown in cobol_unknown_list:
                if cobol_unknown.get_name() == ideal_program.get_name():
                    # we have a match
                    link = ('matchLink', cobol_unknown, ideal_program)
                    links.append(link)

        #2.  for cobol_unknown in application.search_objects(['CAST_COBOL_SavedProgram']):
        try:
            for cobol_known in application.objects().has_type('CAST_COBOL_SavedProgram'):
                cobol_known_list[cobol_known.get_name()] = cobol_known
                logging.debug("Cobol CAST_COBOL_SavedProgram found: {}".format(cobol_known.get_name()))
        except:
            pass
        
            
        logging.info("****** Number of Cobol Programs Found {}".format(str(len(cobol_known_list))))

        try:
            for pli_main in application.objects().has_type('PLIMainProcedure'):
                logging.info("PLIMainProcedure found: {}".format(pli_main.get_name()))
                pli_main_list[pli_main.get_name()] = pli_main
        except:
            pass

        logging.info("****** Number of PLIMainProcedure {}".format(str(len(pli_main_list))))


        try:
            for asm in application.objects().has_type('ASMZOSProgram'):
                logging.info("ASMZOSProgram found: {}".format(asm.get_name()))
                asm_list[asm.get_name()] = asm
        except:
            pass


        logging.info("****** Number of ASMZOSProgram {}".format(str(len(asm_list))))

        for o in application.objects().has_type('ideal_program'):
            ideal_programs[o.get_name()] = o
      

        logging.info("****** Scan Ideal Programs for Calls to Cobol/PLI/ASM")

        try:
            srcFiles = application.get_files(['ideal_program'])
        except Exception:
            logging.error("Error Reading Source file ", str(Exception))
           

        for o in srcFiles:
            logging.info(" File is " + str(o))
    
        #   check if file is analyzed source code, or if it generated (Unknown)
            if not o.get_path():
                continue
                
            ref = ReferenceFinder()
            references = []

            ref.add_pattern('CommentedLine', before='', element ="^\:", after='') 
            ref.add_pattern('calltoprogram', before='', element ="^[\t ]+CALL+\s+([A-Za-z0-9#$@_\-]+)+\s+", after='') 

            try:
                references += [reference for reference in ref.find_references_in_file(o)]
            except FileNotFoundError:
                logging.warning(" Wrong file or path" + str(o))  
            
            #           logging.info("references is " + str(len(references)))
            non_ideal_program_name = ""
            caller_object = ""
            caller_bookmark = ""
            
            for reference in references:
                if reference.pattern_name=='CommentedLine':
                    pass
                elif reference.pattern_name=='calltoprogram':
                    tot_name = reference.value.split()
                    non_ideal_program_name = tot_name[1]
                    logging.info("Probable Non ideal Program found is  " + str(non_ideal_program_name))
                    caller_object = reference.object
                    caller_bookmark = reference.bookmark
            
            
                #                logging.info("caller_bookmark--> " + str(caller_bookmark))
                #logging.info("caller_object--> " + str(caller_object))

                if non_ideal_program_name != "":
                    try:
                        for keyvalue in pli_main_list.items():
                            p0 = keyvalue[0]
                            p1 = keyvalue[1]
                            if p0.strip() == non_ideal_program_name.strip():
                                link = ("callLink", caller_object, p1, caller_bookmark)
                                if link not in links:
                                    links.append(link)
                    except:
                        pass
                    
                    try:
                        for keyvalue in cobol_known_list.items():
                            p0 = keyvalue[0]
                            p1 = keyvalue[1]
                            if p0.strip() == non_ideal_program_name.strip():
                                link = ("callLink", caller_object, p1, caller_bookmark)
                                if link not in links:
                                    links.append(link)
                    except:
                        pass
                    
                    try:
                        for keyvalue in asm_list.items():
                            p0 = keyvalue[0]
                            p1 = keyvalue[1]
                            if p0.strip() == non_ideal_program_name.strip():
                                link = ("callLink", caller_object, p1, caller_bookmark)
                                if link not in links:
                                    links.append(link)
                    except:
                        pass

                    caller_object = ""
                    caller_bookmark = ""
        
        for link in links:
            logging.info("Link to be created is " + str(link))
            create_link(*link) 
            nbLinkCreated += 1
                
        logging.info("****** Number of created matchLink/callLink between ideal_program --> cobol/pli/asm : {}".format(str(nbLinkCreated)))
  