# Import all auxilliary modules
from abaqus import *
from abaqusConstants import *
from part import *
from material import *
from section import *
from assembly import *
from caeModules import *
from step import *
from regionToolset import *
from interaction import *
from load import *
from mesh import *
import numpy as np
import json


sim_name = "{{ sim_name }}"

with open(sim_name+'.json', 'r') as f:
    data = json.load(f)

boxsize = data['boxsize'][0]
meshSize = data['meshsize'][0]

# # # create part

myModel = mdb.models['Model-1']
s = myModel.ConstrainedSketch(name='__profile__', sheetSize=boxsize*2)
g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
s.sketchOptions.setValues(decimalPlaces=6)
s.rectangle(point1=(-0.5*boxsize, -0.5*boxsize), point2=(0.5*boxsize, 0.5*boxsize))
myModel.Part(dimensionality=THREE_D, name='Part-1', type=DEFORMABLE_BODY)
myPart = myModel.parts['Part-1']
myPart.BaseSolidExtrude(depth=boxsize, sketch=s)
del myModel.sketches['__profile__']

# # # assembly
myAsm = myModel.rootAssembly
myAsm.DatumCsysByDefault(CARTESIAN)
myAsm.Instance(dependent=OFF, name='Part-1', part=myPart)
partAsm = myAsm.instances['Part-1']
myAsm.translate(instanceList=('Part-1', ), vector=(boxsize/2., boxsize/2., 0))
# # # mesh
myAsm.seedPartInstance(size=meshSize, regions=(partAsm, ))
myAsm.setElementType(
    elemTypes=(ElemType(elemCode=C3D8RT, 
                        elemLibrary=EXPLICIT,
                        secondOrderAccuracy=OFF, 
                        kinematicSplit=AVERAGE_STRAIN, 
                        hourglassControl=DEFAULT, 
                        distortionControl=DEFAULT, 
                        elemDeletion=ON), ),
    regions=(partAsm.cells,))
myAsm.generateMesh(regions=(partAsm,))

#----------- 02_model_setting.py --------------#
jobName = sim_name

# time scale
Kt = float(data['Kt'][0])
# mass scale
Km = float(data['Km'][0])

# for radiation
emissivity = 0.65 # float(data['emissivity'][0])
# dummy expansion
thermalExpansion = float(data['thermal_exp'][0])

# # # step definition
nIntervals = 100 
method = 'bc' # 'bc', 'radiation', 'film'
initTempPart = data['initTemp'][0]
initTempOven = data['initTemp'][0]
finalTemp = data['finalTemp'][0]
simTime =  data['time'][0]

# # # material definition
matName = 'mat_'+str(data['mat_name'][0])#'18CrNiMo7-6'
matFile = "{{ matfile }}"

# # # amplitude
ampName = 'linear'



# # # temperature method
method = data['method'][0]
#----------------------------#

if ampName == 'linear':
    myModel.TabularAmplitude(data=((0,initTempOven), (simTime, finalTemp)), name='linear', smooth=SOLVER_DEFAULT, timeSpan=STEP)


varList = ('E','ENER','HFL','HFLA','HTL','HTLA','NT','PEEQ','RF','RFL','S','SDV','STATUS','TEMP','TEMPMAVG','U', 'EVOL')

myModel = mdb.models['Model-1']
myPart = myModel.parts['Part-1']
myAsm  = myModel.rootAssembly
partAsm = myAsm.instances['Part-1']

# # # predefined material prop from file
def getMaterialClass(matName):
    with open('mat_data/werkstoffe.csv') as f:
        lines = f.read().rsplit('\n')
        for line in lines:
            words = line.split(';')
            if words[1] == matName[4:]:
                return words[2]
    return None
def defineDensity(matClass):
    density = []
    with open('mat_data/dichte.csv') as f:
        lines = f.read().rsplit('\n')
        for line in lines:
            words = line.split(';')
            if len(words) < 2:
                continue
            if words[2] == matClass:
                density.append((float(words[1]) * 1e-12 * Km, float(words[0])))
    myMat.Density(table=density, temperatureDependency=ON)
            
def defineConductivity(matClass):
    cond = []
    with open('mat_data/Temperaturleitfaehigkeit.csv') as f:
        lines = f.read().rsplit('\n')
        for line in lines:
            words = line.split(';')
            if len(words) < 2:
                continue
            if words[2] == matClass:
                cond.append((float(words[1]), float(words[0])))
    myMat.Conductivity(table=cond, temperatureDependency=ON)
    
def defineSpecificHeat(matClass):
    specHeat = []
    with open('mat_data/Waermekapazitaet.csv') as f:
        lines = f.read().rsplit('\n')
        for line in lines:
            words = line.split(';')
            if len(words) < 2:
                continue
            if words[2] == matClass: ### 1e6
                specHeat.append((float(words[1]) * 1e6 /Kt /Km, float(words[0])))
    myMat.SpecificHeat(table=specHeat, temperatureDependency=ON)

def defineExpansion(matClass):
    myMat.Expansion(table=((thermalExpansion,), ))
    
myModel.Material(name=matName)  
myMat = myModel.materials[matName]              
matClass = getMaterialClass(matName)
defineDensity(matClass)
defineConductivity(matClass)
defineSpecificHeat(matClass)
defineExpansion(matClass)

# myMat.Elastic(table=((210000.0, 0.3), ))
# myMat.Plastic(table=((542.2,0),(549.5,0.001),(550.1,0.001111),(550.7,0.001234),
# (551.4,0.00137),(552.1,0.001522),(552.9,0.00169),(553.7,0.001877),
# (554.6,0.002084),(555.5,0.002315),(556.6,0.002571),(557.7,0.002856),
# (558.9,0.003172),(560.2,0.003522),(561.7,0.003912),(563.2,0.004345),
# (564.8,0.004826),(566.6,0.005359),(568.5,0.005952),(570.6,0.006611),
# (572.8,0.007342),(575.2,0.008154),(577.8,0.009057),(580.6,0.01006),
# (583.6,0.01117),(586.8,0.01241),(590.2,0.01378),(593.9,0.0153),
# (597.8,0.017),(602,0.01888),(606.4,0.02097),(611.1,0.02329),
# (616.1,0.02586),(621.5,0.02872),(627.1,0.0319),(633,0.03543),
# (639.2,0.03935),(645.7,0.0437),(652.4,0.04854),(659.5,0.05391),
# (666.9,0.05987),(674.6,0.06649),(682.5,0.07385),(690.8,0.08202),
# (699.4,0.09109),(708.4,0.1012),(717.7,0.1124),(727.4,0.1248),
# (737.6,0.1386),(748.3,0.1539),(759.6,0.171),(771.6,0.1899),
# (784.3,0.2109),(797.8,0.2342),(812.2,0.2601),(827.6,0.2889),
# (844,0.3209),(861.6,0.3564),(880.4,0.3958),(900.5,0.4396),
# (922,0.4882),(945.1,0.5422),(969.7,0.6022),(996.1,0.6688),
# (1024,0.7428),(1054,0.825),(1087,0.9163),(1121,1.018),
# (1158,1.13),(1198,1.255),(1240,1.394),(1285,1.548),
# (1334,1.72),(1385,1.91),(1441,2.121),(1500,2.356),
# (1564,2.617),(1631,2.906),(1704,3.227),(1782,3.585)))

    
# # # create section
myModel.HomogeneousSolidSection(material=matName, name='Section-1', 
    thickness=None)
myPart.SectionAssignment(region=Region(cells=myPart.cells), sectionName='Section-1')
# # # define surface sets
myAsm.Surface(name='xmin', side1Faces=partAsm.faces.getByBoundingBox(xMax=0))
myAsm.Surface(name='xmax', side1Faces=partAsm.faces.getByBoundingBox(xMin=boxsize))
myAsm.Surface(name='ymin', side1Faces=partAsm.faces.getByBoundingBox(yMax=0))
myAsm.Surface(name='ymax', side1Faces=partAsm.faces.getByBoundingBox(yMin=boxsize))
myAsm.Surface(name='zmin', side1Faces=partAsm.faces.getByBoundingBox(zMax=0))
myAsm.Surface(name='zmax', side1Faces=partAsm.faces.getByBoundingBox(zMin=boxsize))

# # # define geometry face sets
myAsm.Set(name='xmin', faces=partAsm.faces.getByBoundingBox(xMax=0))
myAsm.Set(name='ymin', faces=partAsm.faces.getByBoundingBox(yMax=0))
myAsm.Set(name='zmin', faces=partAsm.faces.getByBoundingBox(zMax=0))



# # # create step & BCs
myModel.XsymmBC(name='xsymm', createStepName='Initial', 
    region=Region(faces = partAsm.faces.getByBoundingBox(xMax=0)))
myModel.YsymmBC(name='ysymm', createStepName='Initial', 
    region=Region(faces = partAsm.faces.getByBoundingBox(yMax=0)))
myModel.ZsymmBC(name='zsymm', createStepName='Initial',
    region=Region(faces = partAsm.faces.getByBoundingBox(zMax=0)))
myModel.TempDisplacementDynamicsStep(improvedDtMethod=ON, name=
    'heat', previous='Initial', timePeriod = simTime)

myModel.setValues(absoluteZero= -273.15, stefanBoltzmann=5.67e-11)
if method == 'bc_edge':
    # # # define geometry edge set for applying bc
    myAsm.Set(name='temp_edge', edges=partAsm.edges.getByBoundingBox(xMin=boxsize, yMin=boxsize))

    myModel.TemperatureBC(name = 'heatBC',
                            amplitude=ampName, 
                            createStepName='heat',
                            distributionType=UNIFORM,
                            fixed=OFF,
                            magnitude=1,
                            region=myAsm.sets['temp_edge'])
elif method == 'radiation':
    myAsm.Surface(name='ymax', side1Faces=partAsm.faces.getByBoundingBox(yMin=boxsize))
    myModel.RadiationToAmbient(name='rad',
                                ambientTemperature=1, 
                                ambientTemperatureAmp=ampName, 
                                createStepName='heat', 
                                distributionType=UNIFORM, 
                                emissivity=emissivity, 
                                field='',  
                                radiationType=AMBIENT, 
                                surface=myAsm.surfaces['ymax'])
    
# # # create predefined temperature
myAsm.Set(name='wholePart', cells=partAsm.cells)
myModel.Temperature(name='Predefined Field-1',
                    createStepName='Initial', 
                    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, 
                    distributionType=UNIFORM, 
                    magnitudes=(initTempPart, ),  
                    region=myAsm.sets['wholePart'])

# # # output request
myModel.fieldOutputRequests['F-Output-1'].suppress()
myModel.FieldOutputRequest(name = 'F-Output-1', createStepName = 'heat',
        region = MODEL, variables = varList, numIntervals = nIntervals)

# create job
myAsm.regenerate()
job = mdb.Job(name=jobName, model=myModel)
job.setValues(activateLoadBalancing=False, numCpus=8, numDomains=8, explicitPrecision=DOUBLE_PLUS_PACK)
job.writeInput()

# # # modify inp file
with open(jobName+'.inp', 'rU') as inpfile:
    lines = inpfile.read().rsplit('\n')
with open(jobName+'.inp', 'w') as outfile:
    for line in lines:
        outfile.write(line+'\n')
        if line == '*Material, name='+matName:
            outfile.write('* INCLUDE, input='+matFile+'\n')
            























