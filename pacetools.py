import xml.etree.ElementTree as ET
import os
import numpy as np


class PACEXML:

    def __init__(self,templateFile):
       
        try:
        
            self.mainTree = ET.parse(templateFile)


            self.constructionElementsClasses = {'wall':'com.hemmis.mrw.pace.model.skin.Wall',
                                                'roof':'com.hemmis.mrw.pace.model.skin.Roof',
                                                'floor':'com.hemmis.mrw.pace.model.skin.Floor',
                                                'transparentElement':'com.hemmis.mrw.pace.model.skin.TransparentElement'}


            self.wallOpaqueCompositions={'Pierre < 40':3,
                                         'Pierre > 40':4,
                                         'Briques/blocs apparents':6,
                                         'Briques/blocs non apparents':7,
                                         'Briques Treillis':8,
                                         'Béton Cellulaire':10,
                                         'Ossature bois':12,
                                         'Cloison légère intérieure':13
                                         }
            
            
            

        except:
            print("could not read PAE file")            

      
    def setTemplatesDir(self,directory):
    
        self.templatesDir = directory
        self.refXMLs = { k:os.path.join(self.templatesDir,k+'_xml.xml') for k in ['wall','roof','floor','transparentElement','facade','wallInstance','floorInstance','roofPlane','roofInstance','opening','layer']}

        self.materials = materials()
        self.materials.read(os.path.join(self.templatesDir,'materials.csv'))
                

    def setMeasurementMethod(self,method):

        acceptablemethodsdict={'projection':'PROJECTION','surfacesbrutes':'MEASUREMENT_GROSS_SURFACE','surfacesnettes':'MEASUREMENT'}

        if method not in acceptablemethodsdict.keys():
            print("Acceptable methods are ",acceptablemethodsdict.keys())
            
            return
       
        methodXMLE=self.mainTree.find('.//surfaceCalculationType')
        methodXMLE.text=acceptablemethodsdict[method]


    def setPrice(self,price):

        priceElem=self.mainTree.find('.//advicePrice')
        if (priceElem is None):
            priceElem = ET.Element('advicePrice')
            self.mainTree.getroot().append(priceElem)

        priceElem.text=str(price)


    def setVPDescription(self,text):
        elem = self.mainTree.find('.//remarkTotalHeatedSpace').find('INITIAL')
        elem.set('class',"java.lang.String")
        elem.text=text

    def setNumberOfFacades(self,number):
        
        valueDict = {1:'ONE_FREE',2:'TWO_FREE',3:'THREE_FREE',4:'DETACHED'}
        
        elem = self.mainTree.find('../freeFacadeCount')
        if elem is None:
            buildingElem = self.mainTree.find('.//building[@id]')
            elem = ET.Element('freeFacadeCount')
        try:
            elem.text= valueDict[number]
            buildingElem.append(elem)
        except:
            print("error in set number of facades")


    def setProcessorInfo(self,number,firstName,lastName,street,houseNumber,zipCode,city,country,email):
        self.mainTree.find("processorNumber").text = number
        self.mainTree.find("processorFirstName").text = firstName
        self.mainTree.find("processorLastName").text = lastName
        self.mainTree.find("processorStreet").text = street
        self.mainTree.find("processorHousenr").text = houseNumber
        self.mainTree.find("processorZipCode").text = zipCode
        self.mainTree.find("processorCity").text = city
        self.mainTree.find("processorCountry").text = country
        self.mainTree.find("processorEMail").text = email


    def addSurfaces(self,surfacesList):    
        # methode des surfaces brutes
        
        #format de surfacesList : 
        #
        #    surfacesList = [ 
        #            {'label':'M1','description':'this is M1', 'environment':'OPEN_AIR','type':'wall','subtype':'FULL','grossArea':100,'grossAreaMod':120},
        #            {'label':'M2','description':'this is M2', 'environment':'OPEN_AIR','type':'wall','subtype':'HOLLOW','grossArea':100,'grossAreaMod':120},
        #            {'label':'P1','description':'this is P1', 'environment':'GROUND','type':'floor','subtype':'-','grossArea':100,'grossAreaMod':120},
        #            {'label':'P2','description':'this is P2', 'environment':'CELLAR_WITH_OPENINGS','type':'floor','subtype':'-','grossArea':100,'grossAreaMod':120},
        #            {'label':'T1','description':'this is T1', 'environment':'OPEN_AIR','type':'roof','subtype':'INCLINED','grossArea':100,'grossAreaMod':120},
        #            {'label':'T2','description':'this is T2', 'environment':'NON_HEATED_SPACE','type':'roof','subtype':'FLAT','grossArea':100,'grossAreaMod':120}
        #            ]
        #
        
        for surface in surfacesList:
        
            self.addConstructionElement(surface['type'],surface['label'],surface['description'],surface['environment'],surface['subtype'])
            self.setGrossSurface(surface['label'],surface['grossArea'])
            self.setGrossSurfaceMod(surface['label'],surface['grossAreaMod'])

    def addNetSurfaces(self,surfacesList):    
        
        for surface in surfacesList:
        
            self.addConstructionElement(surface['type'],surface['label'],surface['description'],surface['environment'],surface['subtype'])
        
        
            if (surface['type'] != 'transparentElement'):
                self.setNetSurface(surface['label'],surface['grossArea'])
                self.setNetSurfaceMod(surface['label'],surface['grossAreaMod'])



    def addFacadesAndSurfaces(self,facadesDict):
        #pour methode des projections
        
        #a ecrire
        
        """ [  {"planType": "Roof|Wall|Floor",
                "planName": "xxx",
                "instances": {
                       "M1": 100,
                       "M2":  50
                       }
                },
               { autre plans ..}
           ]
        """
            

    def addFacade(self,Direction,area):
        
        facadeElem = self.getTemplateElement('facade')
        skin = facadeElem.find('.//skin')
        skin.set('reference',self.mainTree.find('.//skin[@id]').attrib['id'])
                                    
        
        
        name = 'Facade '+str(Direction)
        
        shortDescription = facadeElem.find('shortDescription')
        shortDescription.text = name
        
        orientationElem = facadeElem.find('orientation').find('INITIAL')
        orientationElem.set('class',"com.hemmis.mrw.pace.model.enums.Orientation")
        orientationElem.text=Direction

        facadeElem.find('orientationManually').find('INITIAL').text="false"
     
        self.setObjectGrossSurface(facadeElem,area,'INITIAL')        
 
       
        wallPlanes = self.mainTree.find('.//wallPlanes[@id]')
        initial = wallPlanes.find('INITIAL')
        
        existingFacades = self.getFacades()
        latestFacadeID = self.getHighestID(existingFacades)
        
        latestNewID=self.renumberTreeOrElem(facadeElem,latestFacadeID+1)
        #self.renumberTreeOrElem(self.mainTree,latestFacadeID+1,latestNewID+1)
        self.renumberMainTreeFromID(latestFacadeID+1,latestNewID+1)
       
        initial.append(facadeElem)
        
        return facadeElem.attrib['id']
        
    
    def addRoofPlane(self,Direction,inclination,area):
        
        roofPlane = self.getTemplateElement('roofPlane')
        
        skin = roofPlane.find('.//skin')
        skin.set('reference',self.mainTree.find('.//skin[@id]').attrib['id'])
        skin.attrib.pop('isCut')
        
        name = 'Pan de toit '+str(Direction)+' '+str(inclination)
        
        shortDescription = roofPlane.find('shortDescription')
        shortDescription.text = name
        
        orientationElem = roofPlane.find('orientation').find('INITIAL')
        orientationElem.set('class',"com.hemmis.mrw.pace.model.enums.Orientation")
        orientationElem.text=Direction

        roofPlane.find('orientationManually').find('INITIAL').text="false"
       
        
        self.setObjectGrossSurface(roofPlane,area,'INITIAL')        

        
        roofPlane.find('slope').find('INITIAL').set('class',"java.math.BigDecimal")
        roofPlane.find('slope').find('INITIAL').text = str(inclination)

    
        roofPlanes = self.mainTree.find('.//roofPlanes[@id]')
        initial = roofPlanes.find('INITIAL')
        
        existingRoofPlanes = self.getRoofPlanes()
        latestRoofPlaneID = self.getHighestID(existingRoofPlanes)
        
        latestNewID=self.renumberTreeOrElem(roofPlane,latestRoofPlaneID+1)
        self.renumberMainTreeFromID(latestRoofPlaneID+1,latestNewID+1)
        #self.renumberTreeOrElem(self.mainTree,latestRoofPlaneID+1,latestNewID+1)


        initial.append(roofPlane)
        
        return roofPlane.attrib['id']
    
    
    def addWallInstance(self,facadeID,wallType,area,suffix=' instance'):
        
        wallID = self.findConstructionElementID(wallType,'wall')
        
        facade = self.mainTree.find('.//*[@id="'+facadeID+'"]')
        
       

        wallInstance = self.getTemplateElement('wallInstance')
       
        initialOpaqueElem = wallInstance.find('opaqueElement').find('INITIAL')
        initialOpaqueElem.set('reference',wallID)
        
        initialOpaqueElem = wallInstance.find('opaqueElement').find('INITIAL')
        initialOpaqueElem.set('reference',wallID)
        initialOpaqueElem.attrib.pop('isCut')
        initialOpaqueElem.attrib.pop('uniqueReference')               

        planeElem = wallInstance.find('plane')
        planeElem.set('reference',facadeID)
        planeElem.attrib.pop('isCut')


        instancesList = facade.find('wallInstances')
        initial = instancesList.find('INITIAL')
        latestID = self.getHighestID(initial)

        self.renumberTreeOrElem(wallInstance,int(latestID)+1)

        #Renumbering main tree
        latestWallInstanceID = self.getHighestID(wallInstance)
        self.renumberMainTreeFromID(latestID+1,latestWallInstanceID+1)


        self.setObjectGrossSurface(wallInstance,area,'INITIAL')        

        wallInstance.find('shortDescription').text = wallType+suffix

        #Inserting the newly created instance
        initial.append(wallInstance)       

        # adding refrence to wallInstance in wallTree
        wallID = self.findConstructionElementID(wallType,'wall')
        
        
        wallElem = self.mainTree.find('.//*[@id="'+str(wallID)+'"]')

        initWallInstances = wallElem.find('wallInstances').find('INITIAL')
        newRef = ET.Element('com.hemmis.mrw.pace.model.skin.WallInstance',{'reference':str(latestID+1)})
        initWallInstances.append(newRef)

        
        #the problem here is that the reference to wall instance occurs before it is defined ! 
        self.reorderIdsAndReferences()


    def addRoofInstance(self,roofPlaneID,roofType,area,suffix=' instance'):
        
        roofID = self.findConstructionElementID(roofType,'roof')

        roofPlane = self.mainTree.find('.//*[@id="'+roofPlaneID+'"]')

        
        instancesList = roofPlane.find('.//roofInstances')
        initial = instancesList.find('INITIAL')
        latestID = self.getHighestID(initial)

        roofInstance = self.getTemplateElement('roofInstance')
       
        initialOpaqueElem = roofInstance.find('opaqueElement').find('INITIAL')
        initialOpaqueElem.set('reference',roofID)
        self.renumberTreeOrElem(roofInstance,int(latestID)+1)
        
        initialOpaqueElem = roofInstance.find('opaqueElement').find('INITIAL')
        initialOpaqueElem.set('reference',roofID)
        initialOpaqueElem.attrib.pop('isCut')
        initialOpaqueElem.attrib.pop('uniqueReference')               

        planeElem = roofInstance.find('plane')
        planeElem.set('reference',roofPlaneID)
        planeElem.attrib.pop('isCut')


        #Renumbering main tree
        latestroofInstanceID = self.getHighestID(roofInstance)
        
        self.renumberMainTreeFromID(latestID+1,latestroofInstanceID+1)
        #self.renumberTreeOrElem(self.mainTree,latestroofInstanceID+1,latestroofInstanceID+1)


        self.setObjectGrossSurface(roofInstance,area,'INITIAL')        
   
        roofInstance.find('shortDescription').text = roofType+suffix

        #Inserting the newly created instance
        initial.append(roofInstance)       

        # adding refrence to roofInstance in roofTree
        roofID = self.findConstructionElementID(roofType,'roof')

               
        roofElem = self.mainTree.find('.//*[@id="'+str(roofID)+'"]')


        initroofInstances = roofElem.find('roofInstances').find('INITIAL')
        newRef = ET.Element('com.hemmis.mrw.pace.model.skin.RoofInstance',{'reference':str(latestID+1)})
        initroofInstances.append(newRef)

        
        #the problem here is that the reference to roof instance occurs before it is defined ! 
        self.reorderIdsAndReferences()


    def setFloorPlaneArea(self,situation,area):

        floorPlane = self.mainTree.find('.//floorPlane') #without annexes, this element is unique! However, it can be defined elsewhere
        
        if 'id' not in floorPlane.attrib.keys():
            #in case it is not defined in teh <floorPlane> elemtn, search for the element with the same id as the first reference
            floorPlane = self.mainTree.find('.//*[@id="'+floorPlane.attrib['reference']+'"]')

        self.setObjectGrossSurface(floorPlane,area,situation)        


    def setObjectGrossSurface(self,objectElement,area,situation):

        objectElement.find('heightManually').find(situation).text="false"
        objectElement.find('widthManually').find(situation).text="false"
        objectElement.find('grossSurfaceManually').find(situation).text='true'
        objectElement.find('grossSurface').find(situation).text=str(area)
        objectElement.find('grossSurface').find(situation).set('class',"java.math.BigDecimal")
        
        
        


    def getFloorPlaneArea(self,situation):

        floorPlane = self.mainTree.find('.//floorPlane') #without annexes, this element is unique! However, it can be defined elsewhere
        
        if 'id' not in floorPlane.attrib.keys():
            #in case it is not defined in teh <floorPlane> elemtn, search for the element with the same id as the first reference
            floorPlane = self.mainTree.find('.//*[@id="'+floorPlane.attrib['reference']+'"]')

        return float(floorPlane.find('grossSurface').find(situation).text)


    def addFloorInstance(self,floorType,area,suffix=' instance'):
                
        floorID = self.findConstructionElementID(floorType,'floor')

        floorPlane = self.mainTree.find('.//floorPlane') #without annexes, this element is unique! However, it can be defined elsewhere
        
        if 'id' not in floorPlane.attrib.keys():
            #in case it is not defined in teh <floorPlane> elemtn, search for the element with the same id as the first reference
            floorPlane = self.mainTree.find('.//*[@id="'+floorPlane.attrib['reference']+'"]')
        
        floorPlaneID = floorPlane.attrib['id']

        
        instancesList = floorPlane.find('floorInstances')
        initial = instancesList.find('INITIAL')
        
        latestID = self.getHighestID(initial)

        floorInstance = self.getTemplateElement('floorInstance')
       
        initialOpaqueElem = floorInstance.find('opaqueElement').find('INITIAL')
        initialOpaqueElem.set('reference',floorID)
        self.renumberTreeOrElem(floorInstance,int(latestID)+1)
        
        initialOpaqueElem = floorInstance.find('opaqueElement').find('INITIAL')
        initialOpaqueElem.set('reference',floorID)
        initialOpaqueElem.attrib.pop('isCut')
        initialOpaqueElem.attrib.pop('uniqueReference')               

        planeElem = floorInstance.find('plane')
        planeElem.set('reference',floorPlaneID)
        planeElem.attrib.pop('isCut')


        #Renumbering main tree
        latestfloorInstanceID = self.getHighestID(floorInstance)
        self.renumberMainTreeFromID(latestID+1,latestfloorInstanceID+1)
        #self.renumberTreeOrElem(self.mainTree,latestID+1,latestfloorInstanceID+1)


        self.setObjectGrossSurface(floorInstance,area,'INITIAL')        
   
        floorInstance.find('shortDescription').text = floorType+suffix

        #Inserting the newly created instance
        initial.append(floorInstance)       

        # adding refrence to floorInstance in floorTree
        floorID = self.findConstructionElementID(floorType,'floor')
        
        floorElem = self.mainTree.find('.//*[@id="'+str(floorID)+'"]')

        initfloorInstances = floorElem.find('floorInstances').find('INITIAL')
        newRef = ET.Element('com.hemmis.mrw.pace.model.skin.FloorInstance',{'reference':str(latestID+1)})
        initfloorInstances.append(newRef)
        
        self.reorderIdsAndReferences()

        
    def reorderIdsAndReferences(self):
        #make sure that reference to an item does not appear before it is defined (element with "id" attribute)
        #if so, the two are inverted
        #apply recursively, since any inversion can cause other inversions
        
        previousCorrection = False
        
        parent_map = {c: p for p in self.mainTree.iter() for c in p}
        
        knownIds = []
        
        for elem in self.mainTree.iter():
            
            if 'id' in elem.attrib.keys() :
                knownIds.append(elem.attrib['id'])
        
                    
            if ('reference' in elem.attrib.keys()):
               
                if elem.attrib['reference'] not in knownIds:

                    
                    elemTag = str(elem.tag) #new instance
                    
                    parentElem = parent_map[elem]
                    parentElem.remove(elem)
                                       
                    
                    originalElement = self.mainTree.find('.//*[@id="'+elem.attrib['reference']+'"]')
                    originalTag = str(originalElement.tag)

                    
                    if (elemTag != originalTag):
        
                        originalElement.tag = elemTag                        
                        elem.tag = originalTag

                        if (originalElement.tag == 'INITIAL'):
                            originalElement.attrib['class'] = originalTag

                        if (elem.tag == 'INITIAL'):
                            elem.attrib['class'] = elemTag

                    parentOfOriginal = parent_map[originalElement]
                    parentOfOriginal.remove(originalElement)
                    
                    parentElem.append(originalElement)
                    parentOfOriginal.append(elem)

                    
                    previousCorrection=True
    
                    break

            
        if previousCorrection:
            
            self.reorderIdsAndReferences()
            
    
    def findConstructionElementID(self,reference,elementType):
                
        if (elementType not in self.constructionElementsClasses.keys()):
            print("Valid element types are",self.constructionElementsClasses.keys())
            return
        else:
            paceClass = self.constructionElementsClasses[elementType]
    
        elementsOfClass = self.mainTree.findall('.//'+paceClass+'[@id]') + self.mainTree.findall('.//*[@class="'+paceClass+'"][@id]')
               
        for element in elementsOfClass:
            
            if (element.find('reference').text == reference):
                return element.attrib['id']
            
        return None
        

    def findOpeningByName(self,openingName):
        
        openings = self.mainTree.findall('.//com.hemmis.mrw.pace.model.skin.Opening[@id]')
        
        
        for o in openings:
            if o.find('shortDescription').text == openingName:
                return o
            
        return None
    

    def getHighestID(self,element):
        #get last ID of element subtree
        
        elementsWithID = element.findall('.//*[@id]')

        if (len(elementsWithID) > 0 ):
        
            #latestID = elementsWithID[-1].attrib['id']
            ids = [ int(x.attrib['id']) for x in elementsWithID]
            highestID = max(ids)

        else:
            highestID = element.attrib['id']
        
        return int(highestID)
        
        
    
    def addConstructionElement(self,elementType,label,description,environment,subtype):

        #environment = OPEN_AIR, NON_HEATED_SPACE,GROUND,_WITH_OPENINGS,CELLAR_WITH_OPENINGS,CELLAR_WITHOUT_OPENINGS,HEATED_SPACE        
        
        elementXMLElement = self.getTemplateElement(elementType)
        elementXMLElement.find('reference').text = label
        elementXMLElement.find('shortDescription').text = description
        elementXMLElement.find('environment').text = environment
        
        skinID = self.mainTree.find('.//skin[@id]').attrib['id']
        elemSkin = elementXMLElement.find('skin')

        if (elemSkin != None):        
            elemSkin.set('reference',skinID)
            if 'isCut' in elemSkin.attrib.keys():
                elemSkin.attrib.pop('isCut')                               
            
       
        environmentAdvice = elementXMLElement.find("environmentAdvice")
        if (environmentAdvice == None):
            environmentAdvice = ET.Element("environmentAdvice")
            elementXMLElement.append(environmentAdvice)
    
        environmentAdvice.text = environment

        self.setSubType(elementXMLElement,elementType,subtype)

        self.insertConstructionElementXML(elementType,elementXMLElement)


    def addPredefinedConstructionElement(self,elementType,label,description,environment,elementTemplateDescription):

        elementXMLElement = self.elemsTemplatesDict[elementType][elementTemplateDescription]
        elementXMLElement.find('reference').text = label
        elementXMLElement.find('shortDescription').text = description
        elementXMLElement.find('environment').text = environment
        
        skinID = self.mainTree.find('.//skin[@id]').attrib['id']
        elemSkin = elementXMLElement.find('skin')

        if (elemSkin != None):        
            elemSkin.set('reference',skinID)
            if 'isCut' in elemSkin.attrib.keys():
                elemSkin.attrib.pop('isCut')                               
            
       
        environmentAdvice = elementXMLElement.find("environmentAdvice")
        if (environmentAdvice == None):
            environmentAdvice = ET.Element("environmentAdvice")
            elementXMLElement.append(environmentAdvice)
    
        environmentAdvice.text = environment

        self.insertConstructionElementXML(elementType,elementXMLElement)



    def insertConstructionElementXML(self,elementType,elementXMLElement):        
        
        constructionElements = self.getConstructionElements()
        latestConstructionElementID = self.getHighestID(constructionElements)

        latestAddedID=self.renumberTreeOrElem(elementXMLElement,latestConstructionElementID+1)
        self.renumberMainTreeFromID(latestConstructionElementID+1,latestAddedID+1)

        constructionElements.append(elementXMLElement)

        pacetags={ 'wall':'walls',
                   'roof':'roofs',
                   'floor':'floors',
                   'transparentElement':'transparentElements'}

        #There are lists of constructions elements elsewhere in the file, they need to be updated
        elemlist=self.mainTree.find('.//skin[@id]').find(pacetags[elementType])
        ET.SubElement(elemlist, self.constructionElementsClasses[elementType], reference=elementXMLElement.attrib['id'])


    def setWallDetails(self,label,thickness=0.30,basisComposition='Pierre < 40',layers=[]):

        wallId = self.findConstructionElementID(label,'wall')
        wallElement = self.mainTree.find('.//*[@id="'+wallId+'"]')
    
        wallSpecs = wallElement.find('wallSpecs')
        
        wallSpecs.find('.//thickness').text = str(thickness)
        wallSpecs.find('.//opaqueComposition/id').text=str(self.wallOpaqueCompositions[basisComposition])
        
        for layerDict in layers:
            self.addLayer(wallElement,layerDict)
    
    
    def addLayer(self,constructionElement,layerDict):
        
        constructionElementLayers = constructionElement.find('.//layers')
        constructionElementOpaqueStructure = constructionElement.find('.//opaqueStructure')
    
        maxID = self.getHighestID(constructionElementLayers)
        newLayerID = maxID+1
    
        layerElement = self.getTemplateElement('layer')
    
        self.renumberTreeOrElem(layerElement,newLayerID)

 
        layerElement.find(".//opaqueStructure").attrib['reference']=constructionElementOpaqueStructure.attrib['id']
        
        materialID,categoryID = self.materials.getMaterialAndCategoryID(layerDict['Material'],layerDict['Category'])
    
        layerElement.find('.//material/id').text=str(materialID)   
        layerElement.find('.//material/materialGroupId').text=str(categoryID)

        
        if (layerDict['lambda'] ==''):
            layerElement.find('lamdaManually').text='false'

        else:        
            layerElement.find('lamda').text=str(layerDict['lambda'])
            layerElement.find('lamdaManually').text='true'
        
        layerElement.find('thickness').text=str(layerDict['thickness'])

        if (layerDict['Description']!=''):
            definition=ET.Element('definition')
            definition.text = layerDict['Description']
            layerElement.append(definition)


        if (layerDict['Category']=='Isolants'):

            insulationStructure=ET.Element('insulationStructure')
            insulationStructure.text = 'CONTINUOUS_INSULATION'
            layerElement.append(insulationStructure)


            if (layerDict['woodfraction']!=''):
                e=layerDict['thickness']
                lam = layerDict['lambda']
                f = layerDict['woodfraction']
                
                U = lam/e * (1-f) + f*0.13/e
                R = 1/U
                
                layerElement.find('rvalueManually').text = "true"
                rvalueElement = ET.Element('rvalue')
                rvalueElement.text= str(R)
                layerElement.append(rvalueElement)

                 
                if (constructionElementOpaqueStructure.find('opaqueElementType').text == 'WALL'):
                    insulationStructure.text = 'WOOD_FRAME'
            
            #        <insulationStructure>WOOD_FRAME</insulationStructure>


                
        latestLayerID = self.getHighestID(layerElement)        
        self.renumberMainTreeFromID(newLayerID,latestLayerID+1)

        
        constructionElementLayers.append(layerElement)


    def addOpeningGrossMethod(self,opening_name,wallType,openingtype,direction,inclination=90):
    
        
        openingElement = self.getTemplateElement('opening')

        lastFileId = self.getHighestID(self.mainTree)
        self.renumberTreeOrElem(openingElement,lastFileId+1)

    
        skinID = self.mainTree.find('.//skin[@id]').attrib['id']
        
        openingElement.find('openingSkin[@isCut]').set('reference',skinID)
        openingElement.find('openingSkin').attrib.pop('isCut')
    
    
        walltypeid = self.findConstructionElementID(wallType,'wall')
        wallclass = 'com.hemmis.mrw.pace.model.skin.Wall'

        openingtypeid = self.findConstructionElementID(openingtype,'transparentElement')
        openingclass= 'com.hemmis.mrw.pace.model.skin.TransparentElement'
    
    
        #print(openingElement.find('./opaqueElement').tag,openingElement.find('./opaqueElement').attrib['class'])
        openingElement.find('./opaqueElement/INITIAL').attrib['class']=wallclass
        openingElement.find('./opaqueElement/INITIAL').attrib['reference']=walltypeid
        openingElement.find('./opaqueElement/INITIAL').attrib.pop('isCut')
        openingElement.find('./opaqueElement/INITIAL').attrib.pop('uniqueReference')
        
        
        openingElement.find('./transparentElement/INITIAL').attrib['class']=openingclass
        openingElement.find('./transparentElement/INITIAL').attrib['reference']=openingtypeid
        openingElement.find('./transparentElement/INITIAL').attrib.pop('isCut')
        openingElement.find('./transparentElement/INITIAL').attrib.pop('uniqueReference')
        
        des=openingElement.find('shortDescription')
        des.text=opening_name
        
        
        openingElement.find('./orientation').find('INITIAL').text=direction
        #openingElement.find('./orientation').find('SECOND').text=direction
        
        
        openings=self.mainTree.find('.//skin[@id]/openings')
        initial=openings.find('./INITIAL')
        initial.append(openingElement)
        
        
        wallelem=self.mainTree.find('.//*[@id="'+walltypeid+'"]')
        transelem=self.mainTree.find('.//*[@id="'+openingtypeid+'"]')
        
        
        wopeningslist=wallelem.find('./openings/INITIAL')
        ET.SubElement(wopeningslist, openingElement.tag, {'reference':openingElement.attrib['id']})
        
        topeningslist=transelem.find('./openings/INITIAL')
        ET.SubElement(topeningslist, openingElement.tag, {'reference':openingElement.attrib['id']})


        # if we dont add the openings in second situation if makes some bugs... 
        wopeningsListSecond = wallelem.find('./openings/SECOND')      
        if (wopeningsListSecond == None):
            wopeningsListSecond = ET.Element('SECOND')
            wallelem.find('./openings').append(wopeningsListSecond)
 
        ref = ET.Element(openingElement.tag,{'reference':openingElement.attrib['id']})
        wopeningsListSecond.append(ref)

        topeningsListSecond = transelem.find('./openings/SECOND')      
        if (topeningsListSecond == None):
            topeningsListSecond = ET.Element('SECOND')
            transelem.find('./openings').append(topeningsListSecond)
 
        ref = ET.Element(openingElement.tag,{'reference':openingElement.attrib['id']})
        topeningsListSecond.append(ref)


        self.reorderIdsAndReferences()


    def addOpeningNetMethod(self,opening_name,openingtype,direction,inclination=90,area=1):
    
        #modified situation: UNCHANGED ; REMOVED; CHANGED; ADDED
        # ADDED: remplir tous les fields "second"
        
        openingElement = self.getTemplateElement('opening')

        lastFileId = self.getHighestID(self.mainTree)
        self.renumberTreeOrElem(openingElement,lastFileId+1)
    
        skinID = self.mainTree.find('.//skin[@id]').attrib['id']
        
        openingElement.find('openingSkin[@isCut]').set('reference',skinID)
        openingElement.find('openingSkin').attrib.pop('isCut')
 
        openingtypeid = self.findConstructionElementID(openingtype,'transparentElement')
        openingclass= 'com.hemmis.mrw.pace.model.skin.TransparentElement'
        
        openingElement.find('./transparentElement/INITIAL').attrib['class']=openingclass
        openingElement.find('./transparentElement/INITIAL').attrib['reference']=openingtypeid
        openingElement.find('./transparentElement/INITIAL').attrib.pop('isCut')
        openingElement.find('./transparentElement/INITIAL').attrib.pop('uniqueReference')
        
        des=openingElement.find('shortDescription')
        des.text=opening_name
        
        openingElement.find('./surface/INITIAL').text=str(area)
        
        openingElement.find('./orientation').find('INITIAL').text=direction

        #on l'ajoute a l'endroit le plus logique, on reorganisera après
        openings=self.mainTree.find('.//skin[@id]/openings')
        initial=openings.find('./INITIAL')
        initial.append(openingElement)
        
        transelem=self.mainTree.find('.//*[@id="'+openingtypeid+'"]')
        
        topeningslist=transelem.find('./openings/INITIAL')
        ET.SubElement(topeningslist, openingElement.tag, {'reference':openingElement.attrib['id']})


        
        topeningsListSecond = transelem.find('./openings/SECOND')      
        if (topeningsListSecond == None):
            topeningsListSecond = ET.Element('SECOND')
            transelem.find('./openings').append(topeningsListSecond)


        openings=self.mainTree.find('.//skin[@id]/openings')
        second=openings.find('./SECOND')
        ref = ET.Element(openingElement.tag,{'reference':openingElement.attrib['id']})
        second.append(ref)
        
        
        ref = ET.Element(openingElement.tag,{'reference':openingElement.attrib['id']})
        topeningsListSecond.append(ref)

        #building --> skin --> openings --> INITIAL
        #building --> skin --> openings --> SECOND
        
        #building --> skin --> constructionElements --> transparentElements --> element XX --> openings --> INITIAL
        #building --> skin --> constructionElements --> transparentElements --> element XX --> openings --> SECOND
        

        self.reorderIdsAndReferences()


    def addOpeningNetMethodMod(self,opening_name,openingtype,direction,inclination=90,area=1):
    
        #adding an opening only in modified situation
        
        openingElement = self.getTemplateElement('opening')
        openingElement.find('./state').text='ADDED'

        lastFileId = self.getHighestID(self.mainTree)
        self.renumberTreeOrElem(openingElement,lastFileId+1)
    
        skinID = self.mainTree.find('.//skin[@id]').attrib['id']
        
        openingElement.find('openingSkin[@isCut]').set('reference',skinID)
        openingElement.find('openingSkin').attrib.pop('isCut')
 
        openingtypeid = self.findConstructionElementID(openingtype,'transparentElement')
        openingclass= 'com.hemmis.mrw.pace.model.skin.TransparentElement'
        
        openingElement.find('./transparentElement/INITIAL').attrib['class']=openingclass
        openingElement.find('./transparentElement/INITIAL').attrib['reference']=openingtypeid
        openingElement.find('./transparentElement/INITIAL').attrib.pop('isCut')
        openingElement.find('./transparentElement/INITIAL').attrib.pop('uniqueReference')
        openingElement.find('./transparentElement/INITIAL').tag = 'SECOND'
        
        des=openingElement.find('shortDescription')
        des.text=opening_name


        surface = openingElement.find('surface')

        surface.find('INITIAL').text = str(area)
        second = ET.Element('SECOND',{'class':'java.math.BigDecimal'})
        second.text = str(area)
        surface.append(second) 
        
        orientation = openingElement.find('orientation')
        second = ET.Element('SECOND',{'class':'com.hemmis.mrw.pace.model.enums.Orientation'})
        second.text = str(direction)
        orientation.append(second) 

        #on l'ajoute a l'endroit le plus logique, on reorganisera après
        openings=self.mainTree.find('.//skin[@id]/openings')
        second=openings.find('./SECOND')
        second.append(openingElement)
        
        transelem=self.mainTree.find('.//*[@id="'+openingtypeid+'"]')
      
        topeningslist=transelem.find('./openings/SECOND')
        ET.SubElement(topeningslist, openingElement.tag, {'reference':openingElement.attrib['id']})
      
        openingtypeid = openingElement.find('transparentElement').find('SECOND').attrib['reference']
        transelem=self.mainTree.find('.//*[@id="'+openingtypeid+'"]')
        netSurface = transelem.find('netSurface')
        
        second = ET.Element('SECOND',{'class':'com.hemmis.mrw.pace.model.ObservableSpecProperty','id':'99999','v':'2'})
        cstate = ET.Element('CURRENT__STATE',{'class':'java.math.BigDecimal'})
        cstate.text = '0'
        second.append(cstate)
        netSurface.append(second)
        

        self.reorderIdsAndReferences()


    def setOpeningAreaMod(self,openingName,modArea):

        #defining changed status and change area for second situation
        openingElement = self.findOpeningByName(openingName)
        openingElement.find('./state').text='CHANGED'
        
        second = ET.Element('SECOND',{'class':"java.math.BigDecimal"})
        second.text = str(modArea)
        openingElement.find('./surface').append(second)


        #find transparentElement and updat its surface
        #remove it from transparent element list
        openingtypeid = openingElement.find('transparentElement').find('INITIAL').attrib['reference']
        transelem=self.mainTree.find('.//*[@id="'+openingtypeid+'"]')
        netSurface = transelem.find('netSurface')
        
        second = ET.Element('SECOND',{'class':'com.hemmis.mrw.pace.model.ObservableSpecProperty','id':'99999','v':'2'})
        cstate = ET.Element('CURRENT__STATE',{'class':'java.math.BigDecimal'})
        cstate.text = '0'
        
        second.append(cstate)
        netSurface.append(second)


    def deleteOpeningMod(self,openingName):
        
        #defining changed status and change area for second situation
        openingElement = self.findOpeningByName(openingName)
        openingElement.find('./state').text='REMOVED'
        openingID = openingElement.attrib['id']

        #remove it from "opengigs" list
        openings=self.mainTree.find('.//skin[@id]/openings')
        secondOpeningsList = openings.find('SECOND')
        elementToDelete = secondOpeningsList.find('*[@reference="'+openingID+'"]')
        secondOpeningsList.remove(elementToDelete)

        #remove it from transparent element list
        openingtypeid = openingElement.find('transparentElement').find('INITIAL').attrib['reference']
        transelem=self.mainTree.find('.//*[@id="'+openingtypeid+'"]')
        secondOpeningsList = transelem.find('openings').find('SECOND') 
        elementToDelete = secondOpeningsList.find('.//*[@reference="'+openingID+'"]')
        secondOpeningsList.remove(elementToDelete)
        
                
        
    def changeOpeningsState(self,state):
        
        openingStateElem = self.mainTree.find('.//openingsState')
        openingStateElem.text = 'CHANGED'

        #ok, il faut changer le openingstate par programmation, sinion il y un bug quan don le modifie
        
        



    def setSubType(self,elemXML,skinType,subType):
        
        if skinType == 'roof':
            subtypeTag = 'roofType'
        elif skinType == 'wall':
            subtypeTag = 'wallType'
        elif skinType == 'floor':
            subtypeTag = 'floorType'
            subType ='OTHER' #methode simplifee par defaut
        else:
            #transparentElements --> do nothing
            return
            
        typeXML = elemXML.find('.//'+subtypeTag)
        typeXML.text = subType


    def getConstructionElements(self):
        
        return self.mainTree.find('.//constructionElements[@id]')
        
    def getFacades(self):
        
        return self.mainTree.find('.//wallPlanes')


    def getRoofPlanes(self):
        
        return self.mainTree.find('.//roofPlanes')



    def getLatestFacadeID(self):
    
        rootElement=self.mainTree.getroot()
        existingFacades=rootElement.findall('.//wallPlanes')[0] 
        
        if (len(list(existingFacades))>0):
            celems_with_id=existingFacades.findall(".//*[@id]")  
            latestid=celems_with_id[-1].attrib['id']

        else:
            latestid=existingFacades.attrib['id']

        latestid=int(latestid)

        return existingFacades,latestid

           
    
    def getTemplateElement(self,elementType):
     
        subTree = ET.parse(self.refXMLs[elementType])  

        return subTree.getroot()


    def loadPredefinedTemplateElements(self,templateFile):
        
        templateXML = PACEXML(templateFile)
        templateElems = templateXML.getConstructionElements() #GET ALL CE FROM TEMPLATE

        self.elemsTemplatesDict={}

        for elementType in ['wall','floor','roof','transparentElement']:

            paceClass = self.constructionElementsClasses[elementType]
  
            elementsOfClass = templateElems.findall('.//'+paceClass+'[@id]') + templateElems.findall('.//*[@class="'+paceClass+'"][@id]')

            elemsDict = {}
            
            for elem in elementsOfClass:
                elemsDict[elem.find('.//shortDescription').text] = elem
                
            self.elemsTemplatesDict[elementType] = elemsDict

    """def getPredefinedTemplateElements(self):
        
        return self.elemsTemplatesDict
    """
    
    def getPredefinedTemplatesElementsList(self):
        
        localDict = {}
        
        for elemType,elemDict in self.elemsTemplatesDict.items():
            localDict[elemType] = list(elemDict.keys())

        return localDict
        
    def renumberTreeOrElem(self,TreeOrElement,newStartID):
    
        if (type(TreeOrElement) == type(ET.ElementTree())):       
            element = TreeOrElement.getroot() 
        else:
            element = TreeOrElement
       
        oldID_to_newID_dict = {}

        initialelementID = element.attrib['id']
        element.attrib['id'] = str(newStartID)
         
        oldID_to_newID_dict[initialelementID]=element.attrib['id']   

        elementsWithID  = element.findall(".//*[@id]")          

        newid = newStartID
       
        for e in elementsWithID:                  
            
            newid+=1
            oldID_to_newID_dict[e.attrib['id']]=str(newid)
            e.attrib['id']=str(newid)

        elementsWithRef = element.findall(".//*[@reference]") 

        for e in elementsWithRef:
            if e.attrib['reference'] in oldID_to_newID_dict.keys(): 
                e.attrib['reference']=oldID_to_newID_dict[e.attrib['reference']]  

        return newid


    def renumberMainTreeFromID(self,startID,newStartID):
        #should somehow be merged with the function above, but issues encountered when trying... 
        
        oldID_to_newID_dict = {}

        elementsWithID  = self.mainTree.findall(".//*[@id]")          
       
        newid = newStartID
                
        for e in elementsWithID:        
        
            if int(e.attrib['id']) >= startID :
                oldID_to_newID_dict[e.attrib['id']] =str(newid)                 
                e.attrib['id']=str(newid)
                newid+=1

        elementsWithRef = self.mainTree.findall(".//*[@reference]") 

        for e in elementsWithRef:
            if e.attrib['reference'] in oldID_to_newID_dict.keys(): 
                e.attrib['reference']=oldID_to_newID_dict[e.attrib['reference']]  


    def setNetSurface(self,label,surfaceArea):

        paceroot=self.mainTree.getroot()
        
        celems=paceroot.findall('.//constructionElements')[0] #findall retuns a list. If one exepects single elem, takes 0 of list

        for c in celems:
            #print(c.find('reference').text)
            
            if (c.find('reference').text == label):
                #print(c.find('reference').text)
                
                grossSurfaceManually=c.find('netSurfaceManually')
                state=grossSurfaceManually.find('./INITIAL/CURRENT__STATE')
                state.text='true'

                grossSurface=c.find('netSurface')
                state=grossSurface.find('./INITIAL/CURRENT__STATE')
                state.text=str(surfaceArea)


    def setNetSurfaceMod(self,label,surfaceArea):

        paceroot=self.mainTree.getroot()
        
        celems=paceroot.findall('.//constructionElements')[0] #findall retuns a list. If one exepects single elem, takes 0 of list

        for c in celems:
            
            if (c.find('reference').text == label):

                grossSurface=c.find('netSurface')
               
                second = ET.Element("SECOND")
                grossSurface.append(second)

                second.set('class', 'com.hemmis.mrw.pace.model.ObservableSpecProperty')
                second.set('id','99999')
                second.set('v','2')
                
                state = ET.Element("CURRENT__STATE")
                second.append(state)
                
                state.set('class','java.math.BigDecimal')
                state.text=str(surfaceArea)

                #manually flag

                netSurfaceManually = c.find('netSurfaceManually')
                
                second = ET.Element("SECOND")
                netSurfaceManually.append(second)

                second.set('class', 'com.hemmis.mrw.pace.model.ObservableSpecProperty')
                second.set('id','99998')
                second.set('v','2')
                
                state = ET.Element("CURRENT__STATE")
                second.append(state)
                
                state.set('class','java.lang.Boolean')
                state.text='true'





    def setGrossSurface(self,label,surfaceArea):

        paceroot=self.mainTree.getroot()
        
        celems=paceroot.findall('.//constructionElements')[0] #findall retuns a list. If one exepects single elem, takes 0 of list

        for c in celems:
            #print(c.find('reference').text)
            
            if (c.find('reference').text == label):
                #print(c.find('reference').text)
                
                grossSurfaceManually=c.find('grossSurfaceManually')
                state=grossSurfaceManually.find('./INITIAL/CURRENT__STATE')
                state.text='true'

                grossSurface=c.find('grossSurface')
                state=grossSurface.find('./INITIAL/CURRENT__STATE')
                state.text=str(surfaceArea)



    def setGrossSurfaceMod(self,label,surfaceArea):

        paceroot=self.mainTree.getroot()
        
        celems=paceroot.findall('.//constructionElements')[0] #findall retuns a list. If one exepects single elem, takes 0 of list

        for c in celems:
            
            if (c.find('reference').text == label):

                grossSurface=c.find('grossSurface')
               
                second = ET.Element("SECOND")
                grossSurface.append(second)

                second.set('class', 'com.hemmis.mrw.pace.model.ObservableSpecProperty')
                second.set('id','999')
                second.set('v','2')
                
                state = ET.Element("CURRENT__STATE")
                second.append(state)
                
                state.set('class','java.math.BigDecimal')
                state.text=str(surfaceArea)


    def setHeatedVolume(self,initHeatedVolume,modifiedHeatedVolume=None):
    
        heatedVolumeXMLE=self.mainTree.find('.//basicHeatedSpace')
        
        initHeatedVolumeXMLE = heatedVolumeXMLE.find('.//INITIAL')
        initHeatedVolumeXMLE.text=str(initHeatedVolume)
        initHeatedVolumeXMLE.attrib['class']='java.math.BigDecimal'
        
        if (modifiedHeatedVolume is not None):
            modifiedHeatedVolumeXMLE = heatedVolumeXMLE.find('.//SECOND')
            
            if (modifiedHeatedVolumeXMLE == None):
                modifiedHeatedVolumeXMLE = ET.Element("SECOND")
                heatedVolumeXMLE.append(modifiedHeatedVolumeXMLE)
            
            modifiedHeatedVolumeXMLE.text=str(modifiedHeatedVolume)
            modifiedHeatedVolumeXMLE.attrib['class']='java.math.BigDecimal'
        
        
    def addFloorLevel(self,levelName,levelFloorArea,situation='init'):
        
        levels = self.mainTree.find('.//levels')
        
        newLevel = ET.Element('com.hemmis.mrw.pace.model.skin.Level',attrib={'id':''})
        ET.SubElement(newLevel,'skin',{'reference':self.mainTree.find('.//skin[@id]').attrib['id']})

        subElementsDict = {'shortDescription':levelName,
                           'heightManually':'false',
                           'widthManually':'false',
                           'surfaceManually':'true',
                           'surface':str(levelFloorArea)} 

        for tag,text in subElementsDict.items():
            subE = ET.SubElement(newLevel,tag)
            subE.text = text
        
        if (situation == 'init'):
            levelsList = levels.find('.//INITIAL')
            levelsList.append(newLevel)
        
        
    def setInertia(self,category,situation='init'):

        acceptable = ['HEAVY','MID_HEAVY','MODERATE_HEAVY','LIGHT']
        
        if category not in acceptable:
            print ("Wrong inertia")
            print ("acceptable values are:")
            [print (x) for x in acceptable]
            return
        
        constructionTypeElem = self.mainTree.find('.//constructionType')

        if situation=='init':
            targetElement = constructionTypeElem.find('INITIAL').find('CURRENT__STATE')
            targetElement.set('class',"com.hemmis.mrw.pace.model.enums.ConstructionType")
            targetElement.text = category
        
    def setWeatherStations(self,temperatureStation='PEB',sunStation='PEB'):
        
        #<weatherStation>STREE_BEAUMONT</weatherStation>
        #<weatherStationSun>DOURBES</weatherStationSun>

        #<weatherStation>PEB</weatherStation>
        #<weatherStationSun>PEB</weatherStationSun>

        weatherStationElement = ET.Element('weatherStation')
        weatherStationElement.text = temperatureStation
        
        sunStationElement = ET.Element('weatherStationSun')
        sunStationElement.text = sunStation
        
        self.mainTree.getroot().append(weatherStationElement)
        self.mainTree.getroot().append(sunStationElement)
        

        
        
    def setInsideTemperature(self,value):
    
        insideTemperatureMethodXMLE=self.mainTree.find('.//insideTemperatureCalculationType')
        
        initialInsideTemperatureMethodXMLE = insideTemperatureMethodXMLE.find('.//INITIAL/CURRENT__STATE')
        initialInsideTemperatureMethodXMLE.text='MANUALLY'
        initialInsideTemperatureMethodXMLE.attrib['class']="com.hemmis.mrw.pace.model.enums.InsideTemperatureCalculationType"
    
        averageInsideTemperatureManuallyXMLE = self.mainTree.find('.//averageInsideTemperatureManually')
        initialAverageInsideTemperatureManuallyXMLE = averageInsideTemperatureManuallyXMLE.find('.//INITIAL/CURRENT__STATE')
        initialAverageInsideTemperatureManuallyXMLE.text = 'true'
        initialAverageInsideTemperatureManuallyXMLE.attrib['class'] = 'java.lang.Boolean'
        
        averageInsideTemperatureXMLE = self.mainTree.find('.//averageInsideTemperature')
        initialaverageInsideTemperatureXMLE = averageInsideTemperatureXMLE.find('.//INITIAL/CURRENT__STATE')
        initialaverageInsideTemperatureXMLE.text = str(value)
        initialaverageInsideTemperatureXMLE.attrib['class']='java.math.BigDecimal'
    
    
        modifiedInsideTemperatureMethodXMLE = insideTemperatureMethodXMLE.find('.//SECOND/CURRENT__STATE')
        
        if (modifiedInsideTemperatureMethodXMLE != None):
            modifiedInsideTemperatureMethodXMLE.text='MANUALLY'
            modifiedInsideTemperatureMethodXMLE.attrib['class']="com.hemmis.mrw.pace.model.enums.InsideTemperatureCalculationType"
    
            modifiedAverageInsideTemperatureManuallyXMLE = averageInsideTemperatureManuallyXMLE.find('.//SECOND/CURRENT__STATE')
            modifiedAverageInsideTemperatureManuallyXMLE.text = 'true'
            modifiedAverageInsideTemperatureManuallyXMLE.attrib['class'] = 'java.lang.Boolean'
            
            modifiedaverageInsideTemperatureXMLE = averageInsideTemperatureXMLE.find('.//SECOND/CURRENT__STATE')
            modifiedaverageInsideTemperatureXMLE.text = str(value)
            modifiedaverageInsideTemperatureXMLE.attrib['class']='java.math.BigDecimal'



    def setPicture(self,imageFile,situation):
        
        imagesElement = self.mainTree.find('.//imageInitial')

        asciiImage = imageProcessor().fileToBase64(imageFile)

        
        if (situation == 'init'):
            
            initialImageXMLE = imagesElement.find('.//INITIAL')
            
            initialImageXMLE.attrib['class']="java.awt.image.BufferedImage"
            initialImageXMLE.text = asciiImage
            
        elif situation == 'mod':
            
            modifiedImageXMLE = imagesElement.find('.//SECOND')


            if (modifiedImageXMLE == None):
                modifiedImageXMLE = ET.Element("SECOND")
                imagesElement.append(modifiedImageXMLE)
            
            modifiedImageXMLE.attrib['class']="java.awt.image.BufferedImage"
            modifiedImageXMLE.text = asciiImage
                
        else:
            return
    
    def setFirstPagePicture(self,imageFile):
        building = self.mainTree.find('.//building[@id]')
        imageElement = building.find('image')
        
        if imageElement is None:
            imageElement = ET.Element('image',attrib={'class':'java.awt.image.BufferedImage'})
        
        asciiImage = imageProcessor().fileToBase64(imageFile)

        imageElement.text = asciiImage
        
        building.append(imageElement)

    def writePaceFile(self,filename):
    
        #
        self.renumberTreeOrElem(self.mainTree,1) 
        self.mainTree.write(filename)

        """import lxml.etree as etree

        x = etree.parse(filename)
        xmlstring=etree.tostring(x, pretty_print=True)

        f=open(filename,'wb')
        f.write(xmlstring)
        f.close()
        """



class imageProcessor:
  
    def fileToBase64(self,imFile):
        
        import base64

        with open(imFile, 'rb') as binary_file:
            binary_file_data = binary_file.read()
            base64_encoded_data = base64.b64encode(binary_file_data)
            base64_message = base64_encoded_data.decode('utf-8')

        return base64_message
    
    
class materials:
    
    def __init__(self):
        
        self.materials={'materialID': np.array([]),
                        'materialName': np.array([]),
                        'materialCategory': np.array([]),
                        'materialCategoryID':np.array([])
                        }
    
        self.Nmaterials = 0
    
    def read(self,fileName):
        
        #classical CSV
        #pandas not available --> using kind of dictionnary of numpy arrays

        a = np.loadtxt(fileName,dtype=str,skiprows=1,delimiter=';',encoding='utf-8')

        nrows,ncols = a.shape
        
        self.nmaterials = nrows
        
        for c,key in zip(range(ncols),self.materials.keys()) :
            self.materials[key] = a[:,c]


    def getMaterialsInCategory(self,categoryName):

        return list(self.materials['materialName'][self.materials['materialCategory'] == categoryName ])

    
    def getCategoryID(self,categoryName):

        
        return self.materials['materialCategoryID'][self.materials['materialCategory'] == categoryName ] [0]
        
    
    def getMaterialAndCategoryID(self,materialName,categoryName):
        
        catID = self.getCategoryID(categoryName)
        
        condition1 = np.array(self.materials['materialCategory'] == categoryName)
        condition2 = np.array(self.materials['materialName'] == materialName)
        
        globalCondition = condition1*condition2
        
        matID = self.materials['materialID'][ globalCondition ][0]


        return matID,catID
    
    
                    

    
def test1(template,outputname):

    #########################
    # Methode des projections
    #########################
    #lecture du template et dossier pour les sous template
    xml = PACEXML(template)
    xml.setTemplatesDir('paceTemplates')

    #ajout de types de parois
    xml.addConstructionElement('wall','M1','This is M1','OPEN_AIR','FULL')
    xml.addConstructionElement('wall','M2','This is M2','OPEN_AIR','FULL')
    xml.addConstructionElement('floor','P1','This is P1','GROUND','')
    xml.addConstructionElement('floor','P2','This is P2','GROUND','')
    xml.addConstructionElement('roof','T1','This is T1','OPEN_AIR','INCLINED')
    xml.addConstructionElement('roof','T2','This is T2','OPEN_AIR','INCLINED')


    #ajout de facade et de surfaces sur ces facades
    roofPlaneID = xml.addRoofPlane('S',35,100) 
    xml.addRoofInstance(roofPlaneID,'T1',50)
    xml.addRoofInstance(roofPlaneID,'T2',50)


    Nid = xml.addFacade('N',100)
    xml.addWallInstance(Nid,'M2',50)
    xml.addWallInstance(Nid,'M1',50)


    Sid = xml.addFacade('S',100)
    xml.addWallInstance(Sid,'M1',50)
    xml.addWallInstance(Sid,'M2',50)

    #pas besoin d'ajouter une facade "sol", elle existe pra defaut, il n'y en a qu'une
    xml.setFloorPlaneArea('INITIAL',100)
    xml.addFloorInstance('P1',50)
    xml.addFloorInstance('P2',50)
    #print("Area ",xml.getFloorPlaneArea('INITIAL'))


    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.xml'))
    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.pae'))

    
    

def test2(template,outputname):    
    
    #############################################
    # Méthode des surfaces brutes (ajout 1 par 1)
    #############################################
    xml = PACEXML(template)
    xml.setTemplatesDir('paceTemplates')

    xml.setMeasurementMethod('surfacesbrutes')


    #ajout de types de parois
    xml.addConstructionElement('wall','M1','This is M1','OPEN_AIR','FULL')
    xml.addConstructionElement('wall','M2','This is M2','OPEN_AIR','FULL')

    xml.addConstructionElement('floor','P1','This is P1','GROUND','')
    xml.addConstructionElement('floor','P2','This is P2','GROUND','')

    xml.addConstructionElement('roof','T1','This is T1','OPEN_AIR','INCLINED')
    xml.addConstructionElement('roof','T2','This is T2','OPEN_AIR','INCLINED')
    
    
    xml.setGrossSurface('M1',50)
    xml.setGrossSurface('M2',50)
    xml.setGrossSurface('P1',50)
    xml.setGrossSurface('P2',50)
    xml.setGrossSurface('T1',50)
    xml.setGrossSurface('T2',50)
    
    
    xml.setHeatedVolume(1000,1200)
    xml.setInsideTemperature(18)
    xml.setPicture('test_picture.png','init')
    
    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.xml'))
    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.pae'))

    

def test3(template,outputname):

    #####################################################################################################################
    # Methode des surfaces brutes - ajout de toutes les surfaces en un seul appel --> utilisé depuis FreeCAD actuellement
    #####################################################################################################################

    xml = PACEXML(template)
    xml.setTemplatesDir('paceTemplates')
    xml.setMeasurementMethod('surfacesbrutes')


    surfacesList = []
    
    surfacesList = [ 
                    {'label':'M1','description':'this is M1', 'environment':'OPEN_AIR','type':'wall','subtype':'FULL','grossArea':100,'grossAreaMod':120},
                    {'label':'M2','description':'this is M2', 'environment':'OPEN_AIR','type':'wall','subtype':'HOLLOW','grossArea':100,'grossAreaMod':120},
                    {'label':'P1','description':'this is P1', 'environment':'GROUND','type':'floor','subtype':'-','grossArea':100,'grossAreaMod':120},
                    {'label':'P2','description':'this is P2', 'environment':'CELLAR_WITH_OPENINGS','type':'floor','subtype':'-','grossArea':100,'grossAreaMod':120},
                    {'label':'T1','description':'this is T1', 'environment':'OPEN_AIR','type':'roof','subtype':'INCLINED','grossArea':100,'grossAreaMod':120},
                    {'label':'T2','description':'this is T2', 'environment':'NON_HEATED_SPACE','type':'roof','subtype':'FLAT','grossArea':100,'grossAreaMod':120}
                    ]

    xml.addSurfaces(surfacesList)


    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.xml'))
    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.pae'))

    

def test4(template,outputname):

    ############################################
    #Methode des surfaces brutes avec fenêtres
    ############################################

    xml = PACEXML(template)
    xml.setTemplatesDir('paceTemplates')

    xml.setMeasurementMethod('surfacesbrutes')

    #ajout de types de parois
    xml.addConstructionElement('wall','M2','mur 2','OPEN_AIR','FULL')

    xml.addConstructionElement('floor','P1','This is P1','GROUND','')
    xml.addConstructionElement('floor','P2','This is P2','GROUND','')

    xml.addConstructionElement('roof','T1','This is T1','OPEN_AIR','INCLINED')
    xml.addConstructionElement('roof','T2','This is T2','OPEN_AIR','INCLINED')

    xml.addConstructionElement('transparentElement','F1','Fenetre 1','OPEN_AIR','')
    xml.addConstructionElement('transparentElement','F2','Fenetre 2','OPEN_AIR','')
    
    xml.addConstructionElement('wall','M1','mur 1','OPEN_AIR','FULL')
       
    xml.setGrossSurface('M1',50)
    xml.setGrossSurface('M2',50)
    xml.setGrossSurface('P1',50)
    xml.setGrossSurface('P2',50)
    xml.setGrossSurface('T1',50)
    xml.setGrossSurface('T2',50)
    
    
    xml.addOpeningGrossMethod('Ouverture 1','M1','F1','N')
    xml.addOpeningGrossMethod('Ouverture 2','M2','F1','W')
    xml.addOpeningGrossMethod('Ouverture 3','M1','F2','S')
        
    xml.setHeatedVolume(1000,1200)
    xml.setInsideTemperature(18)
    xml.setPicture('test_picture.png','init')
    
    
    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.xml'))
    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.pae'))


def test4b(template,outputname):

    ############################################
    #Methode des surfaces nettes avec fenêtres
    ############################################

    xml = PACEXML(template)
    xml.setTemplatesDir('paceTemplates')

    xml.setMeasurementMethod('surfacesnettes')

    #ajout de types de parois
    xml.addConstructionElement('wall','M2','mur 2','OPEN_AIR','FULL')
    xml.addConstructionElement('floor','P1','This is P1','GROUND','')
    xml.addConstructionElement('floor','P2','This is P2','GROUND','')

    xml.addConstructionElement('roof','T1','This is T1','OPEN_AIR','INCLINED')
    xml.addConstructionElement('roof','T2','This is T2','OPEN_AIR','INCLINED')

    xml.addConstructionElement('transparentElement','F1','Fenetre 1','OPEN_AIR','')
    xml.addConstructionElement('transparentElement','F2','Fenetre 2','OPEN_AIR','')
    
    xml.addConstructionElement('wall','M1','mur 1','OPEN_AIR','FULL')
       
    xml.setNetSurface('M1',50)
    xml.setNetSurface('M2',50)
    xml.setNetSurface('P1',50)
    xml.setNetSurface('P2',50)
    xml.setNetSurface('T1',50)
    xml.setNetSurface('T2',50)
    

    
    xml.addOpeningNetMethod('Ouverture 1','F1','N')  
    xml.addOpeningNetMethod('Ouverture 2','F1','W')
    xml.addOpeningNetMethod('Ouverture 3','F2','S')
        
    xml.setHeatedVolume(1000,1200)
    xml.setInsideTemperature(18)
    xml.setPicture('test_picture.png','init')
    
    
    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.xml'))
    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.pae'))


def test4c(template,outputname):

    ################################################################
    #Methode des surfaces nettes avec fenêtres et situation modifiee
    ################################################################

    xml = PACEXML(template)
    xml.setTemplatesDir('paceTemplates')

    xml.setMeasurementMethod('surfacesnettes')

    #ajout de types de parois
    xml.addConstructionElement('wall','M2','mur 2','OPEN_AIR','FULL')
    xml.addConstructionElement('floor','P1','This is P1','GROUND','')
    xml.addConstructionElement('floor','P2','This is P2','GROUND','')

    xml.addConstructionElement('roof','T1','This is T1','OPEN_AIR','INCLINED')
    xml.addConstructionElement('roof','T2','This is T2','OPEN_AIR','INCLINED')

    xml.addConstructionElement('transparentElement','F1','Fenetre 1','OPEN_AIR','')
    xml.addConstructionElement('transparentElement','F2','Fenetre 2','OPEN_AIR','')
    
    xml.addConstructionElement('wall','M1','mur 1','OPEN_AIR','FULL')
       
    xml.setNetSurface('M1',50)
    xml.setNetSurface('M2',50)
    xml.setNetSurface('P1',50)
    xml.setNetSurface('P2',50)
    xml.setNetSurface('T1',50)
    xml.setNetSurface('T2',50)
    xml.setNetSurfaceMod('T2',62)

    
    xml.addOpeningNetMethod('Ouverture 1','F1','N',area=1.2)  
    xml.addOpeningNetMethod('Ouverture 2','F1','W',area=1.3)
    xml.addOpeningNetMethod('Ouverture 3','F2','S',area=1.4)
        
    xml.changeOpeningsState('CHANGED')
    xml.setOpeningAreaMod('Ouverture 1',3.14)
    xml.deleteOpeningMod('Ouverture 2')    

    xml.addOpeningNetMethodMod('Ouverture 4','F2','NW',area=1.707)

    
    xml.setHeatedVolume(1000,1200)
    xml.addFloorLevel('Rez de chaussee',142,'init')
    xml.setInertia('MODERATE_HEAVY')
    xml.setWeatherStations()
    
    xml.setInsideTemperature(18)
    xml.setPicture('test_picture.png','init')
    xml.setFirstPagePicture('test_picture.png')

    

    
    xml.setPrice(900)
    xml.setVPDescription("C'est le volume protégé")
    xml.setNumberOfFacades(4)    
    
    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.xml'))
    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.pae'))

    print("Test 4 c completed")
    
    
def test5(template,outputname):
    
    ############################################
    # Elements avec couches
    ############################################


    xml = PACEXML(template)
    xml.setTemplatesDir('paceTemplates')

    xml.setMeasurementMethod('surfacesbrutes')

    #ajout de types de parois
   
    xml.addConstructionElement('wall','M1','mur 1','OPEN_AIR','FULL')
    #xml.addConstructionElement('wall','M2','mur 2','OPEN_AIR','FULL')


    layer1 = {'Category':'Isolants',
             'Material':'Laine minérale (MW)',
             'Description':'Laine minérale fb=0.1',
             'lambda':0.035,
             'thickness':0.1,
             'R':'',
             'woodfraction':0.1}


    layer2 = {'Category':'Isolants',
             'Material':'Laine minérale (MW)',
             'Description':'Laine minérale continue',
             'lambda':0.035,
             'thickness':0.12,
             'R':'',
             'woodfraction':''}

    layer3 = {'Category':'Blocs creux (intérieurs)',
             'Material':'Blocs creux de béton (19 cm)',
             'Description':'Bloc 19',
             'lambda':'',
             'thickness':0.19,
             'R':'',
             'woodfraction':''}

 
    xml.setWallDetails('M1',0.19,'Pierre < 40',[layer1,layer2,layer3])
    

    xml.setGrossSurface('M1',50)
   
    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.xml'))
    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.pae'))


def test6(template,outputname):

    #ajout d'éléments prédéfinis depuis un template
    
    xml = PACEXML(template)
    xml.setTemplatesDir('paceTemplates')

    ceTemplateFile = 'constructionElementsDataBase.xml'
    xml.loadPredefinedTemplateElements(os.path.join('paceTemplates',ceTemplateFile))


    existingElements = xml.getPredefinedTemplatesElementsList()

    print(existingElements)
   
    #def addPredefinedConstructionElement(self,elementType,label,description,environment,elementTemplateDescription):
    #ajout de types de parois
    xml.addPredefinedConstructionElement('wall','MNEW','This is an imported wall from library','OPEN_AIR','Mur pierre 50')
    xml.addPredefinedConstructionElement('roof','TOLD','This is an imported wall from library','OPEN_AIR','Ardoise ou tuiles sans sous toiture')
    
    
    
    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.xml'))
    xml.writePaceFile(os.path.join('paceToolsTestDir',outputname+'.pae'))

    



def main():
    
    outputTestDir = 'paceToolsTestDir'
    if ( not os.path.exists(outputTestDir) ):
        os.mkdir(outputTestDir)
    
    
    template = os.path.join('paceTemplates','audit_vierge.xml')
    templateMazout = os.path.join('paceTemplates','ccMazout_template.xml')
    templatePasdeChauffage = os.path.join('paceTemplates','aucunSysteme_template.xml')

    """test1(template,'testProjection')
    test2(template,'testGross')
    test3(template,'testGrossAllInOne')
    """
    #test4(template,'testGrossWindows')
    #test4b(template,'testNetWindows')
    test4c(templatePasdeChauffage,'testNetWindowsMod')

    """test5(template,'testLayers')
    
    test1(templateMazout,'testMazout')

    test1(templatePasdeChauffage,'testNoHeating')
    """    
    
    test6(template,'testWithTemplates')
    


if __name__ == "__main__":
    # execute only if run as a script
    main()
