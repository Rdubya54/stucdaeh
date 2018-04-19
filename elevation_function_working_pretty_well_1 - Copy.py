import arcpy
import os
import string
import math
from arcpy import env
from arcpy.sa import *
from random import *

GAP_DETECTOR=50

#Row class consists of a head of row, indicating first point in row within the sort;
#row_coord, the coordinate of the row; row_list, a list of lists of all the id's
#contained by eached section of the row; section_list a list of all the id's
#in each section. Once a new section is detected the old section list is appened
#to the row list
class Row:
        def __init__(self,head_of_row,row_coord,section_coord):
                arcpy.AddMessage("row is "+str(head_of_row))
                self.row_coord=row_coord
                self.section_id_list=[]
                self.section_coord_list=[]
                self.row_id_list=[]
                self.row_coord_list=[]
                
        def append_point(self,object_id,section_coord):
                self.section_id_list.append(object_id)
                self.section_coord_list.append(section_coord)
                
        def append_section(self):
                self.row_id_list.append(self.section_id_list)
                self.row_coord_list.append(self.section_coord_list)
                self.section_id_list=[]
                self.section_coord_list=[]
                        
class Low_elev_point:

        def __init__(self,object_id,elevation,section_coord,row_coord,coordused):
                self.object_id=object_id
                self.elevation=elevation
                self.row_coord=row_coord
                self.section_coord=section_coord
                self.coordused=coordused

class Point:
        
        def __init__(self,object_id,section_coord,row_coord,elevation):
                
                self.object_id=object_id
                self.row_coord=row_coord
                self.section_coord=section_coord
                self.elevation=elevation
                self.in_network=False

class Network_node(Point):

        draworder=0

        def __init__(self,objectid,section_coord,row_coord,coordused,elevation):
                #increment draw order everytime new instance is created
                Network_node.draworder+=1
                arcpy.AddMessage("Draw order:"+str(Network_node.draworder)+"created \n with ID:"+str(objectid))
                self.ID=objectid
                self.row_coord=row_coord
                self.section_coord=section_coord
                self.coordused=coordused
                self.draworder=Network_node.draworder
                self.elevation=elevation

class Networklist(list):

        networklist=[]
        new_point_flag=True

        def __init__(self):
                pass
                
        def add_to_network(self,candidate):

                try:
                        arcpy.AddMessage("new_point_flag is "+str(self.new_point_flag))
                        row_coord=networklist[-1].row_coord
                        section_coord=networklist[-1].section_coord
                        new_row_coord=candidate.row_coord
                        new_section_coord=candidate.section_coord
                        validity=self.test_distance(row_coord,section_coord,new_row_coord,new_section_coord)

                        if validity==False and self.new_point_flag==False:
                                arcpy.AddMessage("aborting adding "+str())
                                self.new_point_flag=True

                        else:
                                networklist.append(candidate)
                                self.new_point_flag=False
                                
                except IndexError:
                        networklist.append(candidate)

        def test_distance(self,row_coord,section_coord,new_row_coord,new_section_coord):

                if (abs(new_row_coord-row_coord)>3 and abs(new_section_coord-section_coord)>3):
                        return False
##                distance=math.sqrt((new_row_coord-row_coord)**2+(new_section_coord-section_coord)**2)

                else:
                        return True

class Subsort_set():

        def __init__(self,sort_type):
                self.sort_type=sort_type
                self.section_id_list=[]
                self.section_coord_list=[]
                self.row_id_list=[]
                self.row_coord_list=[]

        def append_point(self,object_id,section_coord):
                self.section_id_list.append(object_id)
                self.section_coord_list.append(section_coord)
                
        def append_section(self):
                self.row_id_list.append(self.section_id_list)
                self.row_coord_list.append(self.section_coord_list)
                self.section_id_list=[]
                self.section_coord_list=[]

def convert_list(listt):
        #remove blanks from export list
        listt=[x for x in listt if x != [[]]]
        string=str(listt)
        almost=string.replace("[","")
        there=almost.replace("]","")
        fixed="("+there+")"
        
        return fixed

def elevation_test(candidate_elevation,networklist):

        if (len(networklist)==0):
                return True
        if ((candidate_elevation-0.1)<=networklist[-1].elevation):
                return True
        else:
                return False
        
#this uses the distance formula to check distance between points in sort and last appended
#network node
def calculate_distance_between_points(first_point,last_point,last_appended,prev_coord):

        if prev_coord=="Y":
                lastappend_y=last_appended.section_coord
                lastappend_x=last_appended.row_coord
                
        else:
                lastappend_y=last_appended.row_coord
                lastappend_x=last_appended.section_coord

##        arcpy.AddMessage("lastappend_Y:"+str(lastappend_y))
##        arcpy.AddMessage("lastappend_x:"+str(lastappend_x))
##
##        arcpy.AddMessage("first point:"+str(first_point))
##        arcpy.AddMessage("last point:"+str(last_point))
        
        first_distance=math.sqrt((first_point[0]-lastappend_x)**2+(first_point[1]-lastappend_y)**2)
        last_distance=math.sqrt((last_point[0]-lastappend_x)**2+(last_point[1]-lastappend_y)**2)

        if first_distance>last_distance:
                arcpy.AddMessage("\n\n RESORT REQUIRED!")
                return True

        else:
                return False

#use this function to confirm that points being added to a sort are adjacent
#to the sort they are being added to
def adj_test(trial_coords,compare_coords):
        
        #if section is congruent with previously appended row in subsort set
        if (abs(max(trial_coords)-max(compare_coords))<5 or (abs(min(trial_coords)-min(compare_coords))<5)):

                return 1

        #if section is not congruent with previously appended row in subsort set
        else:
                arcpy.AddMessage("Flagged as unadjacent")
                return 0
        
                
#use this function to divide points collected for subsort into two different subsorts
def divide_subsort_into_two_parts(networklist,previous_row,subsortset,subsort_adj_ref,other_subsortset):

        first_section_dict=dict(zip(previous_row.row_id_list[0],previous_row.row_coord_list[0]))
        last_section_dict=dict(zip(previous_row.row_id_list[-1],previous_row.row_coord_list[-1]))

        if len(first_section_dict)==0:

                arcpy.AddMessage("first section length flagged as zero")
                distance_from_first=1
                distance_from_last=0

        else:
        
                first_avg=sum(first_section_dict.values())/len(first_section_dict)
                last_avg=sum(last_section_dict.values())/len(last_section_dict)

                distance_from_first=abs(subsort_adj_ref-first_avg)
                distance_from_last=abs(subsort_adj_ref-last_avg)
                
        if distance_from_first>distance_from_last:

                try:
                        result=adj_test(last_section_dict.values(),other_subsortset.row_coord_list[-1][-1])

                except:
                        result=1

                #if result =1 do what would normally be done and remove section from subsort and load into
                #other subsort
                if result==1:

                        try:
                                
                                del subsortset.row_id_list[-1]

                        except:
                                pass
                        
                        other_subsortset.append_point(last_section_dict.keys(),last_section_dict.values())
                        other_subsortset.append_section()

                        return 1

        else:      
                try:
                        result=adj_test(first_section_dict.values(),subsortset.row_coord_list[-1][-1])

                except:
                        result=1

                #if result =1 do what would normally be done and remove section from subsort and load into
                #other subsort
                if result==1:

                        try:

                                del other_subsortset.row_id_list[-1]

                        except:
                                pass
                        
                        subsortset.append_point(first_section_dict.keys(),first_section_dict.values())
                        subsortset.append_section()
                        
                        return 0

def subsort(subsortset,networklist,sorttable,coordused,sort_command,lastappend_row_coord):

        search_fields=["NEAR_FID","POINT_X","POINT_Y","grid_code","Direction_of_Flow","OG_OID"]

        if subsortset is None:
                arcpy.AddMessage("\t\t\t\tIn a NORMAL sort\n\n")
                subsorttable=sorttable

        else:
                if len(subsortset.row_id_list)==0:
                        return networklist

                arcpy.AddMessage("\t\t\t\tIn a subsort\n\n")

                last_append_coord=networklist[-1].row_coord

                fixed=convert_list(subsortset.row_id_list)

                arcpy.AddMessage("Fixed is "+str(fixed))
                #make feature layer of just points in subsort set
                rando=str(randint(0,100))
                subsort_lyr=arcpy.MakeFeatureLayer_management(sorttable,"mayor"+rando,"OG_OID IN "+fixed)

                arcpy.AddMessage("sort is"+str(rando))
                
                #subsort these points into a sort table
                subsorttable=os.path.join(env.workspace,naming+"_subsorttable_"+str(counter)+rando)

                prev_coord=coordused

                if sort_command=="change":

                        if coordused=="Y":
                                arcpy.Sort_management(subsort_lyr, subsorttable, [["POINT_X", "ASCENDING"],["POINT_Y","DESCENDING"]])
                                coordused="X"
                                resort_method="DESCENDING"

                        elif coordused=="X":
                                arcpy.Sort_management(subsort_lyr, subsorttable, [["POINT_Y", "DESCENDING"],["POINT_X","DESCENDING"]])
                                coordused="Y"
                                resort_method="ASCENDING"
                                
                else:
                        if coordused=="Y":
                                arcpy.Sort_management(subsort_lyr, subsorttable, [["POINT_Y", "DESCENDING"],["POINT_X","DESCENDING"]])
                                coordused="Y"
                                resort_method="ASCENDING"

                        elif coordused=="X":
                                arcpy.Sort_management(subsort_lyr, subsorttable, [["POINT_X", "ASCENDING"],["POINT_Y","DESCENDING"]])
                                coordused="X"
                                resort_method="DESCENDING"

                sort_counter=0

                with arcpy.da.SearchCursor(subsorttable,search_fields) as deciding_cursor:

                        for row in deciding_cursor:

                                if sort_counter==0:

                                        first_point=(row[1],row[2])
                                                
                                        sort_counter+=1

                                else:
                                        last_point=(row[1],row[2])

                try:

                        resort_required=calculate_distance_between_points(first_point,last_point,networklist[-1],prev_coord)


                        if resort_required==True:

                                arcpy.Delete_management(subsorttable)

                                if coordused=="Y":
                                        
                                        arcpy.Sort_management(subsort_lyr, subsorttable, [["POINT_Y", resort_method],["POINT_X","DESCENDING"]])

                                else:
                                        arcpy.Sort_management(subsort_lyr, subsorttable, [["POINT_X", resort_method],["POINT_Y","DESCENDING"]])

                except:
                        arcpy.AddMessage("First point")
                                
        is_first_indicator=False
        adjfound=False
        subsortneeded_flag=False
        firstrow_flag=True
        cancel_network_node=False
        gapsbeingcollected=False
        multicolumnrow=False
        newrow=False
        
        firstrow_tracker=None
        previousappend_section_coord=None
        previousappend_row_coord=None
        new_row_tracker=None
        new_section_tracker=None
        current_row=None
        
        lowestelev=Low_elev_point(None,None,None,None,None)
        adj_lowestelev=Low_elev_point(None,None,None,None,None)
        
        consecutive_segment_counter=0
        
        subsortset=Subsort_set("normal")
        other_subsortset=Subsort_set("other")
        subsort_points=[]
        network_list=[]

        #create list of point objects in sort
        with arcpy.da.SearchCursor(subsorttable,search_fields) as objectcursor:

                for row2 in objectcursor:

                        #depending on what coord we are sorting by,
                        #assign the proper attributes to point objects
                        if coordused=="X":
                                subsort_points.append(Point(row2[5],row2[2],row2[1],row2[3]))

                        elif coordused=="Y":
                                subsort_points.append(Point(row2[5],row2[1],row2[2],row2[3]))     

        arcpy.AddMessage("coordused is"+str(coordused))

        #iterate through list sorted point objects  

        for point in subsort_points:

                #once code as moved away from first row it begin to operate as normal
                #flip the boolean to allow this
                if (firstrow_tracker!=None and firstrow_tracker!=point.row_coord):
                        firstrow_flag=False
                #if code is at the beginnning of the stream
                if (new_row_tracker==None):

                        #if this is the very first point on a point also in the first row
                        #that has a lower elev than than the very first point
                        if (lowestelev.elevation==None or lowestelev.elevation>point.elevation):

                                previousappend_section_coord=point.section_coord
                                previousappend_row_coord=point.row_coord

                                current_row=Row(point.object_id,point.row_coord,point.section_coord)

                                #always make lowestelev.elevation the elev of first point in new row
                                lowestelev=Low_elev_point(point.object_id,point.elevation,point.row_coord,point.section_coord,coordused)
                                adj_lowestelev=Low_elev_point(point.object_id,point.elevation,point.row_coord,point.section_coord,coordused)
                                
                                firstrow_tracker=point.section_coord

                                new_row_tracker=point.row_coord
                                new_section_tracker=point.section_coord
                
                #if code is in new X row
                elif (new_row_tracker!=point.row_coord):

                        arcpy.AddMessage(str(point.object_id))

                        current_row.append_section() 
                                
                        previous_row=current_row
                        current_row=Row(point.object_id,point.row_coord,point.section_coord)

                        #we will only collect head of row if there is only one section
                        current_row.append_point(point.object_id,point.section_coord)

                        newrow=True
                        
                        if subsortneeded_flag==True:

                                subsortset.append_section()

                                arcpy.AddMessage("gapping")

                                sortorder=divide_subsort_into_two_parts(networklist,previous_row,subsortset,subsort_adj_ref,other_subsortset)

                                #if the previous row had no multicolumns stop collecting for subsort
                                #this is for when the code is done with the bend competely
                                if multicolumnrow==False:
                                        subsortneeded_flag=False

                                        #if only one row of points was collectected
                                        #abandon subsort
                                        if (consecutive_segment_counter>1):
                                                
                                                fixed=convert_list(list(subsortset.row_id_list))

                                                lyr=arcpy.MakeFeatureLayer_management(mem_point,"slayer","OBJECTID IN "+fixed)

                                                arcpy.CopyFeatures_management(lyr,os.path.join(env.workspace,naming+"_"+naming+"subsort"))

                                                if sortorder==0:
                                                        arcpy.AddMessage("Lauching same other subsort on set"+str(other_subsortset.row_id_list))
                                                        subsort(other_subsortset,networklist,sorttable,coordused,"same",networklist[-1].row_coord)
                                                        arcpy.AddMessage("Launching change OG subsort on set "+str(subsortset.row_id_list))
                                                        subsort(subsortset,networklist,sorttable,coordused,"change",networklist[-1].row_coord)
                                                        
                                                else:
                                                        arcpy.AddMessage("Launching same OG subsort on set "+str(subsortset.row_id_list))
                                                        subsort(subsortset,networklist,sorttable,coordused,"same",networklist[-1].row_coord)
                                                        arcpy.AddMessage("Launching change other subsort on set "+str(other_subsortset.row_id_list))
                                                        subsort(other_subsortset,networklist,sorttable,coordused,"change",networklist[-1].row_coord) 

                                        consecutive_segment_counter=0
                                        subsortset=Subsort_set("normal")
                                        other_subsortset=Subsort_set("other")
                                        gapsbeingcollected=False

                        if multicolumnrow==False:

                                #if lowestelev_adj wasn't the same point as lowest elev in previous row
                                #add to the network list too
                                arcpy.AddMessage("adj i is "+str(adj_lowestelev.object_id))
                                arcpy.AddMessage("reg i is "+str(lowestelev.object_id))
                                if (adj_lowestelev.object_id!=lowestelev.object_id and adj_lowestelev.object_id!=None):
         
                                        #add the object id of the lowest elev in previous row to network list
                                        networklist.add_to_network(Network_node(adj_lowestelev.object_id,adj_lowestelev.section_coord,adj_lowestelev.row_coord,adj_lowestelev.coordused,adj_lowestelev.elevation))
                                        if (elevation_test(lowestelev.elevation,networklist)==True):
                                                networklist.add_to_network(Network_node(lowestelev.object_id,lowestelev.section_coord,lowestelev.row_coord,lowestelev.coordused,lowestelev.elevation))

                                #if instead the lowestelev was the same as lowestadjacent
                                else:
                                        if adj_lowestelev.object_id==None:
                                                if (elevation_test(lowestelev.elevation,networklist)==True):
                                                        networklist.add_to_network(Network_node(lowestelev.object_id,lowestelev.section_coord,lowestelev.row_coord,lowestelev.coordused,lowestelev.elevation))

                                        else:
                                                networklist.add_to_network(Network_node(lowestelev.object_id,lowestelev.section_coord,lowestelev.row_coord,lowestelev.coordused,lowestelev.elevation))
                                        
                        #give code the new adjaceny reference point now that it is a new row
                        previousappend_section_coord=networklist[-1].section_coord
                        previousappend_row_coord=networklist[-1].row_coord
                        
                        #always make lowestelev the elev of first point in new row
                        lowestelev=Low_elev_point(point.object_id,point.elevation,point.row_coord,point.section_coord,coordused)                      

                        #reset this since you aren't sure if your in a multicolumnrow yet
                        multicolumnrow=False
                        
                        #reset boolean for preventing last column subsort rows from being
                        #extracted as nodes twice
                        cancel_network_node=False

                        #reset adjecny lowest elevs, otherwise they will accidently be used in new row
                        adj_lowestelev=Low_elev_point(None,1000000000000,None,None,None)
                        
                        #if this point also happens to be adjacent to previously append
                        #network point
                        if (previousappend_row_coord!=None and abs(point.section_coord-previousappend_row_coord)<=1.5):

                                adj_lowestelev=Low_elev_point(point.object_id,point.elevation,point.row_coord,point.section_coord,coordused) 
                                

                #if code is in same X row        
                else:
                        #if a segment x column is detected
                        if(abs(point.section_coord-new_section_tracker)>GAP_DETECTOR):

                                arcpy.AddMessage(str(point.object_id))

                                #start a new section list for the list of section lists with the row
                                current_row.append_section()

                                #start a new section list for subsort
                                subsortset.append_point(current_row.row_id_list[-1],current_row.row_coord_list[-1])
                                subsortset.append_section()
                                
                                current_row.append_point(point.object_id,point.section_coord)

                                if gapsbeingcollected==False:
                                        subsort_adj_ref=networklist[-1].row_coord
                                        gapsbeingcollected=True

                                #raise alarm to collect points for subsort
                                subsortneeded_flag=True
                                
                                #raise an alarm that this a multicolumn row
                                multicolumnrow=True

                                arcpy.AddMessage("True")

                                firstgap_in_row=True

                                #keep resetting all lowest elev records each time new x column is dectected
                                #so that only last
                                #ycolumn segemnt will get collected
                                lowestelev=Low_elev_point(point.object_id,point.elevation,point.row_coord,point.section_coord,coordused)

                                adj_lowestelev=Low_elev_point(None,1000000000000,None,None,None)

                                #newrow insures that consectuivesegemntcounter
                                #is only being incremented once per row
                                if (newrow==True):
                                        consecutive_segment_counter+=1
                                        newrow=False

                        else:
                                current_row.append_point(point.object_id,point.section_coord)
                                        
                        #if point is at lower elev than current lowestelev, make this point
                        #the new lowest elev
                        if lowestelev.elevation>point.elevation:
                                lowestelev=Low_elev_point(point.object_id,point.elevation,point.row_coord,point.section_coord,coordused)
##                                arcpy.AddMessage("lowest elev is"+str(point.object_id))

                        #if this point also happens to be adjacent to previously append
                        #network point AND its lower than current lowestelev_adj
##                        arcpy.AddMessage("point section coord is"+str(point.section_coord))
##                        arcpy.AddMessage("prev section coord is"+str(previousappend_row_coord))
                        
                        if (abs(point.section_coord-previousappend_row_coord)<=1.5 and adj_lowestelev.elevation>point.elevation):

                                adj_lowestelev=Low_elev_point(point.object_id,point.elevation,point.row_coord,point.section_coord,coordused)
##                                arcpy.AddMessage("lowest ADJ elev is"+str(point.object_id))
                                        
                #as long we are not just still in first row of stream
                if (firstrow_flag==False):
                        #track previous X coord here so you know when x/y row changes
                        new_row_tracker=point.row_coord
                        new_section_tracker=point.section_coord

                #if subsort is needed, collect points for subsort
                #by putting object id of points in list
                if subsortneeded_flag==True:

                        #add point for subsort
                        subsortset.append_point(point.object_id,point.section_coord)

        if subsortneeded_flag==True:

                arcpy.AddMessage("\n\n \t\t We outhrer \n\n")

                try:

                        if sortorder==0:
                                arcpy.AddMessage("Lauching same other subsort on set"+str(other_subsortset.row_id_list))
                                subsort(other_subsortset,networklist,sorttable,coordused,"same",networklist[-1].row_coord)
                                arcpy.AddMessage("Launching change OG subsort on set "+str(subsortset.row_id_list))
                                subsort(subsortset,networklist,sorttable,coordused,"change",networklist[-1].row_coord)
                                
                        else:
                                arcpy.AddMessage("Launching same OG subsort on set "+str(subsortset.row_id_list))
                                subsort(subsortset,networklist,sorttable,coordused,"same",networklist[-1].row_coord)
                                arcpy.AddMessage("Launching change other subsort on set "+str(other_subsortset.row_id_list))
                                subsort(other_subsortset,networklist,sorttable,coordused,"change",networklist[-1].row_coord)
                except:
                        pass
                

        return networklist

#################################################################################################################################################################

env.overwriteOutput = True
arcpy.SetLogHistory(False)
arcpy.CheckOutExtension("3D")
arcpy.CheckOutExtension("spatial")

#get parameters
AC_points=arcpy.GetParameterAsText(0)
streamlines=arcpy.GetParameterAsText(1)
env.workspace=r"in_memory/jeff"
naming=arcpy.GetParameterAsText(3)

#save points and lines into memory for faster processing
##mem_points=arcpy.CopyFeatures_management(AC_points,r"in_memory/AC_points")
##mem_line=arcpy.CopyFeatures_management(streamlines,r"in_memory/streamlines")

#copy OID field in points for later use
arcpy.AddMessage("copying oids")
arcpy.AddField_management(AC_points, "OG_OID", "INTEGER")
arcpy.CalculateField_management(AC_points, "OG_OID","!OBJECTID!", "PYTHON_9.3")

#give points NEAR_FID
arcpy.Near_analysis(AC_points, streamlines)

#make in_mem copies into layers
mem_point=arcpy.MakeFeatureLayer_management(AC_points,"pointz")
mem_lines=arcpy.MakeFeatureLayer_management(streamlines,"linez")

#load xy coordinates of points into their attribute table
arcpy.AddXY_management(mem_point)

#get number of input streamlines (not mem_lines because then object id's wont match up right)
countingstreamlines=arcpy.GetCount_management(streamlines)
streamlinecount=int(countingstreamlines.getOutput(0))

arcpy.AddMessage("sreamlines count is "+str(streamlinecount))

#add field to points to hold Flow Direction
arcpy.AddField_management(mem_point, "Direction_of_Flow", "TEXT")

arcpy.AddField_management(mem_point, "neighbor_x", "FLOAT")
arcpy.AddField_management(mem_point, "neighbor_y", "FLOAT")
arcpy.AddField_management(mem_point, "neighbor_id", "FLOAT")
arcpy.AddField_management(mem_point, "draworder", "INTEGER")
#####################################################################

counter=1

#points with the current streamlines OBJECT ID as the NEAR_FID
#are the only points selected
#make a sorted table out of them and iterate through it
networklist=Networklist()

#start iterating through streamlines OIDs, writing in the OBJECTID of nearest streamline
#in each point's attribute table. 
while counter<=streamlinecount:

        arcpy.AddMessage("line counter is "+str(counter))

        #select stream with same OID as counter
        arcpy.SelectLayerByAttribute_management(mem_lines, "NEW_SELECTION","OBJECTID = "+str(counter))

        #check to make sure a stream got selected
        countingselected=arcpy.GetCount_management(mem_lines)
        selectedcount=int(countingselected.getOutput(0))

        if selectedcount==0:
                counter+=1
                continue

        #(grid code is elevation of point)
        insert_fields=["Direction_of_Flow"]
        search_streams=["Direction_of_Flow","OBJECTID"]

        #grab Flow Direction and OID value from selected streamline
        with arcpy.da.UpdateCursor(mem_lines, (search_streams)) as streamsearchcursor:
                for row in streamsearchcursor:
                       Direction=row[0]
                       arcpy.AddMessage("direction is "+str(Direction))
                       streamsearchcursor.updateRow(row)

        del streamsearchcursor

        #select all points with the same NEAR_FID as counter
        arcpy.SelectLayerByAttribute_management(mem_point, "NEW_SELECTION","NEAR_FID = "+str(counter))
        counting=arcpy.GetCount_management(mem_point)
        count=int(countingstreamlines.getOutput(0))
        arcpy.AddMessage("count is "+str(count))

        #increment streamlinecount
        counter+=1

        if count>0:
                
                #insert flow direction value into points 
                with arcpy.da.InsertCursor(mem_point, (insert_fields)) as insert:
                                
                        for row in mem_point:
                                arcpy.AddMessage("og_OID here is"+str(Direction))
                                insert.insertRow([str(Direction)])

                del insert

        else:
                arcpy.AddMessage("contiuning")
                continue


        #make destination to save sortedtable
##        sorttable=r"in_memory/sorttable"+str(counter)
        env.workspace=arcpy.GetParameterAsText(2)
        sorttable=os.path.join(env.workspace,naming+"_sorttable_"+str(counter))
        
        #sort table will be sorted by the necessary coordiante
        #and ascending elevation value
        if Direction=="N" or Direction=="NE" or Direction=="NW":
                
                arcpy.Sort_management(mem_point, sorttable, [["POINT_Y", "ASCENDING"],["POINT_X","ASCENDING"]])
                coordused="Y"

        elif Direction=="S" or Direction=="SE" or Direction=="SW":
                
                arcpy.Sort_management(mem_point, sorttable, [["POINT_Y", "DESCENDING"],["POINT_X","DESCENDING"]])
                coordused="Y"
                
        elif Direction=="W":
                
                arcpy.Sort_management(mem_point, sorttable, [["POINT_X", "DESCENDING"],["POINT_Y","DESCENDING"]])
                coordused="X"
        
        elif Direction=="E":
                
                arcpy.Sort_management(mem_point, sorttable, [["POINT_X", "ASCENDING"],["POINT_Y","ASCENDING"]])
                coordused="X"

        else:
                continue
        
        subsortset=None
        subsort(subsortset,networklist,sorttable,coordused,"same",None)

        extractiondict={}
        extractionlist=[]

        #transfer network_node objects id's into a list
        #so that we can easily select them out with select
        #by attribute
        for node in networklist:
                extractionlist.append(node.ID)
                extractiondict[node.ID]=node.draworder
                
        string=str(extractionlist)
        almost=string.replace("[","")
        there=almost.replace("]","")
        fixed="("+there+")"

        env.workspace=arcpy.GetParameterAsText(2)

        arcpy.SelectLayerByAttribute_management(mem_point, "CLEAR_SELECTION")
                                                
        lyr=arcpy.MakeFeatureLayer_management(mem_point,"slayer","OBJECTID IN "+fixed)

        search_fields=["NEAR_FID","POINT_X","POINT_Y","grid_code","Direction_of_Flow","OG_OID","draworder"]

        with arcpy.da.UpdateCursor(lyr,search_fields) as drawcursor:

                for row3 in drawcursor:
                              
                        key=row3[5]

                        try:

                                #theres an ERROR HERE KEYERROR:2
                                row3[6]=extractiondict[key]
                        
                                drawcursor.updateRow(row3)

                        except:
                                arcpy.AddMessage("key is not in draw order dict"+str(key))
                                

        arcpy.CopyFeatures_management(lyr,os.path.join(env.workspace,naming+"_"+"HC_network"))

arcpy.Delete_management(mem_point)
arcpy.Delete_management(mem_lines)
arcpy.Delete_management(lyr)
