import arcpy
import os
import string
import math
from arcpy import env
from arcpy.sa import *
from random import *

GAP_DETECTOR=2
DISTANCE_LIMIT=5

#Row class consists of a head of row, indicating first point in row within the sort;
#row_coord, the coordinate of the row; row_list, a list of lists of all the id's
#contained by eached section of the row; section_list a list of all the id's
#in each section. Once a new section is detected the old section list is appened
#to the row list
class Row:
        '''This for dividing up the entire input areas into rows. The area is then analazyed
        row by row, point by point'''
        def __init__(self,head_of_row,row_coord,section_coord):
                arcpy.AddMessage("row is "+str(head_of_row))
                self.row_coord=row_coord
                self.section_id_list=[]
                self.section_coord_list=[]
                self.row_id_list=[]
                self.row_coord_list=[]
                self.node_row_id=None
                self.node_row_coord=None

        def append_point(self,object_id,section_coord):
                self.section_id_list.append(object_id)
                self.section_coord_list.append(section_coord)
##                arcpy.AddMessage("list is "+str(self.section_id_list))

##                if object_id==1938:
##                        import sys
##                        sys.exit()

        def append_section(self):
                self.row_id_list.append(self.section_id_list)
                self.row_coord_list.append(self.section_coord_list)
                self.section_id_list=[]
                self.section_coord_list=[]

        #appends the coords and id of the row that network node is upon it's creation
        def append_node_row(self,index):
                self.node_row_id=self.row_id_list[index]
                self.node_row_coord=self.row_coord_list[index]
                
class Low_elev_point:

        def __init__(self,object_id,elevation,section_coord,row_coord,coordused,dist):
                self.object_id=object_id
                self.elevation=elevation
                self.row_coord=row_coord
                self.section_coord=section_coord
                self.coordused=coordused
                self.dist=dist

class Point:

        def __init__(self,object_id,section_coord,row_coord,elevation):

                self.object_id=object_id
                self.row_coord=row_coord
                self.section_coord=section_coord
                self.elevation=elevation
                self.in_network=False

class Network_node(Point):

        draworder=0

        def __init__(self,objectid,section_coord,row_coord,coord_used,elevation):

                try:
                        arcpy.AddMessage("object coordused is "+str(coord_used))
                        prev_row_coord=networklist[-1].row_coord
                        prev_section_coord=networklist[-1].section_coord
                        coordused=networklist[-1].coordused
                        new_row_coord=row_coord
                        new_section_coord=section_coord
                        new_coordused=coord_used
                        

                        validity=self.test_distance(prev_row_coord,prev_section_coord,new_row_coord,new_section_coord,coordused,new_coordused)

                        if validity==True:

                                #increment draw order everytime new instance is created
                                Network_node.draworder+=1
                                arcpy.AddMessage("Draw order:"+str(Network_node.draworder)+"created \n with ID:"+str(objectid))
                                
                                self.ID=objectid
                                self.row_coord=row_coord
                                self.section_coord=section_coord
                                self.coordused=coordused
                                self.draworder=Network_node.draworder
                                self.elevation=elevation
                                
                                networklist.add_to_network(self)

                                if Network_node.draworder==273:
                                        arcpy.AddMessage("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
##                                        import sys
##                                        sys.exit()

                        elif validity==False:
                                arcpy.AddMessage("candidate point rejected")

                except IndexError:
                        arcpy.AddMessage("must be first point i guess")

                        #increment draw order everytime new instance is created
                        Network_node.draworder+=1
                        arcpy.AddMessage("Draw order:"+str(Network_node.draworder)+"created \n with ID:"+str(objectid))
                        self.ID=objectid
                        self.row_coord=row_coord
                        self.section_coord=section_coord
                        self.coordused=coord_used
                        self.draworder=Network_node.draworder
                        self.elevation=elevation
                        
                        networklist.add_to_network(self)

        def test_distance(self,row_coord,section_coord,new_row_coord,new_section_coord,coordused,new_coordused):

                arcpy.AddMessage("new row coord "+str(new_row_coord))
                arcpy.AddMessage("row coord "+str(row_coord))
                arcpy.AddMessage("section coord "+str(section_coord))
                arcpy.AddMessage("new section coord "+str(new_section_coord))
                arcpy.AddMessage("coorused: "+str(coordused))
                arcpy.AddMessage("newcoorused: "+str(new_coordused))

                difference_1=abs(new_section_coord-section_coord)
                difference_2=abs(new_section_coord-row_coord)

                if ((difference_1<DISTANCE_LIMIT or difference_2<DISTANCE_LIMIT) and (difference_1>0 and difference_2>0)):
                        return True

                else:
                        return False

##
##                if Network_node.draworder==21:
##                        import sys
##                        sys.exit()
class Networklist(list):

        def __init__(self):
                pass

        def add_to_network(self,candidate):

                self.append(candidate)

class Subsort_set():

        def __init__(self,sort_type):
                self.sort_type=sort_type
                self.section_id_list=[]
                self.section_coord_list=[]
                self.row_id_list=[]
                self.row_coord_list=[]

        def append_point(self,object_id,section_coord):
                self.section_id_list.append(object_id)
##                arcpy.AddMessage("subsection id list is:"+str(self.section_id_list))
                self.section_coord_list.append(section_coord)

        def append_section(self):
                if len(self.section_id_list)>0:
                        self.row_id_list.append(self.section_id_list)
                        arcpy.AddMessage("subsort list is:"+str(self.row_id_list))
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

#if at any one time in the first five rows, the code sees
#n number of points in one row. it will throw up alert sort was started on a subsort
def subsort_at_start_test(subsort_points):

        row_count=0
        point_count=0
        prev_row_count=0

        for point in subsort_points:

                if row_count==0:
                        previous_row_coord=point.row_coord
                        row_count+=1
                        
                elif point.row_coord!=previous_row_coord:
                        prev_row_count=row_count
                        row_count+=1
                        point_count=0

                        if row_count==6:
                                return True
                        
                point_count+=1
                previous_row_coord=point.row_coord

                if point_count>15:
                        return False

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
                arcpy.AddMessage("last append was "+str(last_appended.ID))
                return True

        else:
                return False

def determine_sort_order(subsort_lyr,coordused,sort_command,is_a_reject,rando):

                search_fields=["NEAR_FID","POINT_X","POINT_Y","grid_code","Direction_of_Flow","OG_OID","draworder"]

                #subsort these points into a sort table
                subsorttable=os.path.join(env.workspace,naming+"_subsorttable_"+str(counter)+rando)

                prev_coord=coordused

                arcpy.AddMessage("sort command is"+str(sort_command))
                if sort_command=="change":

                        if coordused=="Y":
                                arcpy.Sort_management(subsort_lyr, subsorttable, [["POINT_X", "ASCENDING"],["POINT_Y","DESCENDING"]])
                                coordused="X"
                                resort_method="DESCENDING"
                                arcpy.AddMessage("\t\t coordused is "+str(coordused))

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
                arcpy.AddMessage("is a reject "+str(is_a_reject))
                if is_a_reject==False:

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

                        except Exception as e:
                                arcpy.AddMessage("First point "+str(e))
                                returned_tuple=(subsorttable,coordused)
                                return returned_tuple
                        
                returned_tuple=(subsorttable,coordused)
                arcpy.AddMessage("returned tuple is "+str(returned_tuple[1]))
                return returned_tuple

def make_subsort_points(subsorttable,coordused):

        subsort_points=[]

        search_fields=["NEAR_FID","POINT_X","POINT_Y","grid_code","Direction_of_Flow","OG_OID","draworder"]

        #create list of point objects in sort
        with arcpy.da.SearchCursor(subsorttable,search_fields) as objectcursor:

                for row2 in objectcursor:

                        #depending on what coord we are sorting by,
                        #assign the proper attributes to point objects
                        if coordused=="X":
##                                arcpy.AddMessage("row coord is point_y")
                                subsort_points.append(Point(row2[5],row2[2],row2[1],row2[3]))

                        elif coordused=="Y":
##                                arcpy.AddMessage("row coord is point_x")
                                subsort_points.append(Point(row2[5],row2[1],row2[2],row2[3]))

                return subsort_points

#use this function to confirm that points being added to a sort are adjacent
#to the sort they are being added to
def row_adj_test(object_id,current_row,previous_row,networklist):

        if previous_row==None:
                return True

        else:
                i=0
                arcpy.AddMessage("object id is "+str(object_id))
                arcpy.AddMessage("row list is "+str(current_row.row_id_list))
                for section in current_row.row_id_list:
                        arcpy.AddMessage("section is"+str(section))
                        if object_id in section:
                                candidate_row=section
                                index=i
                                break

                        i+=1
                arcpy.AddMessage("index is "+str(index))
                candidate_coords=current_row.row_coord_list[index]
                previous_coords=previous_row.node_row_coord
##                other_previous_coords=previous_row.node_section_coord

##                arcpy.AddMessage("Can ID's"+str(current_row.row_id_list[index]))
##                arcpy.AddMessage("Prev ID's"+str(previous_row.row_id_list[index]))
                arcpy.AddMessage("Candidate coords are"+str(candidate_coords))
##                arcpy.AddMessage("Previous coords are "+str(previous_coords))

                if len(previous_coords)!=0:
                        

                        #if section is congruent with previously appended row in subsort set
                        if (abs(max(candidate_coords)-max(previous_coords))<5 or (abs(min(candidate_coords)-min(previous_coords))<5)):

                                return True

##                        elif (abs(max(candidate_coords)-max(other_previous_coords))<5 or (abs(min(candidate_coords)-min(otber_previous_coords))<5)):
##                                return True

                        #if section is not congruent with previously appended row in subsort set
                        else:
                                arcpy.AddMessage("Flagged as unadjacent")
                                return False

                else:
                        return True

def delete_network_row(node_objectid,subsortset):

        for section in subsortset.row_id_list:
                if node_objectid in section:
                        arcpy.AddMessage("deleted "+str(section))
                        del section

                        return subsortset

        return subsortset

#takes row list of lowest elevs in each section and
#appends the one that is closest to the previous network node
def append_network_node(row_lowelev_list,current_row,previous_row):

        min_dist=999999999999999999999
        i=0
        foundone=False
        
        for point in row_lowelev_list:
                if point.dist<min_dist:
##                        if row_adj_test(point.object_id,current_row,previous_row)==True:
                        lowestelev=row_lowelev_list[i]
                        min_dist=lowestelev.dist
                        index=i
                        foundone=True
                i+=1
        #if a viable point has been found append it
        if foundone==True:
                arcpy.AddMessage("function coord used is "+str(lowestelev.coordused))
                Network_node(lowestelev.object_id,lowestelev.section_coord,lowestelev.row_coord,lowestelev.coordused,lowestelev.elevation)
                current_row.append_node_row(index)
                return True

        else:
                return False
                
def subsort(subsortset,networklist,sorttable,coordused,sort_command,lastappend_row_coord):

        rando=str(randint(0,100))
        result=None

        search_fields=["NEAR_FID","POINT_X","POINT_Y","grid_code","Direction_of_Flow","OG_OID"]

        if subsortset is None:
                arcpy.AddMessage("\t\t\t\tIn a NORMAL sort\n\n")
                subsort_lyr=sorttable
                arcpy.AddMessage("coord used is "+str(coordused))

        else:
                if len(subsortset.row_id_list)==0:
                        return networklist

                arcpy.AddMessage("\t\t\t\tIn a subsort\n\n")

                last_append_coord=networklist[-1].row_coord

                fixed=convert_list(subsortset.row_id_list)

                arcpy.AddMessage("Fixed is "+str(fixed))
                #make feature layer of just points in subsort set
                subsort_lyr=arcpy.MakeFeatureLayer_management(sorttable,"mayor"+rando,"OG_OID IN "+fixed)

                arcpy.AddMessage("sort is"+str(rando))

        returned_tuple=determine_sort_order(subsort_lyr,coordused,sort_command,False,rando)
        subsort_table=returned_tuple[0]
        coordused=returned_tuple[1]
        arcpy.AddMessage("coord used is 2"+str(coordused))

        #lauch test to insure sort is not started on subsort region
        subsort_points=make_subsort_points(subsort_table,coordused)
        arcpy.AddMessage("coord used is 3"+str(coordused))

        #only need to test for this if we are at beginning of line in intial sort
        if subsortset==None:
                result=subsort_at_start_test(subsort_points)

        #steps taken to resort if sort starts out in subsort
        if result==False:
                arcpy.AddMessage("coord used is 4"+str(coordused))
                returned_tuple=determine_sort_order(subsort_lyr,coordused,"change",True,rando)
                subsort_table=returned_tuple[0]
                coordused=returned_tuple[1]
                arcpy.AddMessage("coord used is 5"+str(coordused))
                subsort_points=make_subsort_points(subsort_table,coordused)

        arcpy.AddMessage("\t\t\t result was "+str(result))
        arcpy.AddMessage("coordused is"+str(coordused))

        is_first_indicator=False
        adjfound=False
        subsortneeded_flag=False
        firstrow_flag=True
        gapsbeingcollected=False
        multicolumnrow=False
        newrow=False
        gap=False
        gap_and_low=False
        prevrow_state=None

        firstrow_tracker=None
        previousappend_section_coord=None
        previousappend_row_coord=None
        new_row_tracker=None
        new_section_tracker=None
        current_row=None

        lowestelev=Low_elev_point(None,None,None,None,None,None)
        adj_lowestelev=Low_elev_point(None,None,None,None,None,None)

        previous_row=None

        consecutive_segment_counter=0

        subsortset=Subsort_set("normal")
        network_list=[]

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
                                lowestelev=Low_elev_point(point.object_id,point.elevation,point.row_coord,point.section_coord,coordused,0)
                                row_lowelev_list=[]

                                firstrow_tracker=point.section_coord

                                new_row_tracker=point.row_coord
                                new_section_tracker=point.section_coord

                #if code is in new row
                elif (new_row_tracker!=point.row_coord):

                        arcpy.AddMessage(str(point.object_id))
                        arcpy.AddMessage(str(prevrow_state))

                        #this if is to prevent first non gap row being appended before
                        #subsort is lauched
                        if prevrow_state==True and multicolumnrow==False:
                                arcpy.AddMessage("in here")
                                pass

                        else:
                                #append the last sections of the previous row to thier respective row lists
                                row_lowelev_list.append(lowestelev)
                                current_row.append_section()
        ##                        arcpy.AddMessage("Row: "+str(current_row.row_id_list))

                                #append network node identified in previous row
                                result=append_network_node(row_lowelev_list,current_row,previous_row)

                        #if there is a gap happening append the last section of the
                        #row to the subsort
                        if subsortneeded_flag==True:

                                subsortset.append_section()

                                #delete section from subsort that containied the appended network node
                                subsortset=delete_network_row(lowestelev.object_id,subsortset)

                        #create new row objects for new row
                        if result==True:
                                previous_row=current_row
                                
                        current_row=Row(point.object_id,point.row_coord,point.section_coord)

                        #only collect head of row if there is only one section
                        current_row.append_point(point.object_id,point.section_coord)

                        newrow=True

                        if subsortneeded_flag==True:

                                #if the previous row had no multicolumns stop collecting for subsort
                                #this is for when the code is done with the bend competely
                                if multicolumnrow==False:
                                        subsortneeded_flag=False

                                        fixed=convert_list(list(subsortset.row_id_list))

                                        lyr=arcpy.MakeFeatureLayer_management(mem_point,"slayer","OBJECTID IN "+fixed)

                                        arcpy.CopyFeatures_management(lyr,os.path.join(env.workspace,naming+"_"+naming+"subsort"))

                                                
                                        arcpy.AddMessage("Launching change OG subsort on set "+str(subsortset.row_id_list))
                                        subsort(subsortset,networklist,sorttable,coordused,"change",networklist[-1].row_coord)

                                        consecutive_segment_counter=0
                                        subsortset=Subsort_set("normal")
                                        gapsbeingcollected=False

                        #give code the new adjaceny reference point now that it is a new row
                        previousappend_section_coord=networklist[-1].section_coord
                        previousappend_row_coord=networklist[-1].row_coord

                        new_section_tracker=point.section_coord

                        row_lowelev_list=[]
                        #always make lowestelev the elev of first point in new row
                        dist=(abs(point.section_coord-previousappend_row_coord))
                        arcpy.AddMessage("right here coord used is "+str(coordused))
                        lowestelev=Low_elev_point(point.object_id,point.elevation,point.row_coord,point.section_coord,coordused,dist)

                        #reset this since you aren't sure if your in a multicolumnrow yet
                        prevrow_state=gap
                        multicolumnrow=False
                        firstrow=True
                        gap=False
                        gap_and_low=False

                #if code is in same X row
                else:
                        arcpy.AddMessage("object id is"+str(point.object_id))
##                        #if a segment x column is detected
##                        arcpy.AddMessage("NST:"+str(new_section_tracker))

                        if(abs(point.section_coord-new_section_tracker)>GAP_DETECTOR or (gap==True)):

                                arcpy.AddMessage("in first if")
                                gap=True

                                if(abs(point.section_coord-new_section_tracker)>GAP_DETECTOR):
                                        point_in_row_counter=1
                                        arcpy.AddMessage("gapped")
                                        gap_and_low=False
                                        current_row.append_section()
                                        row_lowelev_list.append(lowestelev)
                                        dist=(abs(point.section_coord-previousappend_row_coord))
                                        lowestelev=Low_elev_point(point.object_id,point.elevation,point.row_coord,point.section_coord,coordused,dist)

                                        if subsortneeded_flag==True:
                                                subsortset.append_point(current_row.row_id_list[-1],current_row.row_coord_list[-1])
                                                subsortset.append_section()

                                if gap_and_low==True:
                                        arcpy.AddMessage("gap and low")
##                                        arcpy.AddMessage("appended "+str(current_row.row_id_list[-1]))
##                                        subsortset.append_point(current_row.row_id_list[-1],current_row.row_coord_list[-1])

                                #to get in this block, point must be at least almost lower then previous append network node
                                #it
                                arcpy.AddMessage((point.elevation-0.05) <= networklist[-1].elevation)

                                gap_and_low=True

                                arcpy.AddMessage("got into elif NE[-1]: "+str(networklist[-1].elevation))

                                #i think i also need to append the -2 row. Nope don't think so

                                if gapsbeingcollected==False:
                                        subsort_adj_ref=networklist[-1].row_coord
                                        gapsbeingcollected=True

                                if len(current_row.row_id_list[-1])>0:
                                        subsortset.append_point(current_row.row_id_list[-1],current_row.row_coord_list[-1])
                                
                                #raise alarm to collect points for subsort
                                subsortneeded_flag=True

                                #raise an alarm that this a multicolumn row
                                multicolumnrow=True

                                firstgap_in_row=True

                                #newrow insures that consectuivesegemntcounter
                                #is only being incremented once per row
                                if (newrow==True):
                                        consecutive_segment_counter+=1
                                        newrow=False
##                        arcpy.AddMessage("adding: "+str(point.object_id))
                        current_row.append_point(point.object_id,point.section_coord)
                        new_section_tracker=point.section_coord

                        #if point is lowest in row found so far...
                        if lowestelev.elevation>point.elevation:
                                #calculate it's distance from last appended to line network
                                dist=(abs(point.section_coord-previousappend_row_coord))

                                #if this value is lower then current lowestelev's dist from last appended line network,
                                #make this point the new lowestelev
                                if dist<lowestelev.dist or dist<1.5:
                                        arcpy.AddMessage("set to lowest"+str(point.object_id))
                                        lowestelev=Low_elev_point(point.object_id,point.elevation,point.row_coord,point.section_coord,coordused,dist)

                #as long we are not just still in first row of stream
                if (firstrow_flag==False):
                        #track previous X coord here so you know when x/y row changes
                        new_row_tracker=point.row_coord

        if subsortneeded_flag==True:

                arcpy.AddMessage("\n\n \t\t We outhrer \n\n")

                try:

                        if sortorder==0:
                                arcpy.AddMessage("Launching change OG subsort on set "+str(subsortset.row_id_list))
                                subsort(subsortset,networklist,sorttable,coordused,"change",networklist[-1].row_coord)

                        else:
                                arcpy.AddMessage("Launching same OG subsort on set "+str(subsortset.row_id_list))
                                subsort(subsortset,networklist,sorttable,coordused,"same",networklist[-1].row_coord)
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
