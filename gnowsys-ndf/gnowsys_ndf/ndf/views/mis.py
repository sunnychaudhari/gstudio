''' -- imports from python libraries -- '''
import os
import ast
# from datetime import datetime
import datetime

''' -- imports from installed packages -- '''
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render_to_response #, render  uncomment when to use
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

try:
    from bson import ObjectId
except ImportError:  # old pymongo
    from pymongo.objectid import ObjectId

''' -- imports from application folders/files -- '''
from gnowsys_ndf.ndf.org2any import org2html
from gnowsys_ndf.ndf.models import node_collection, triple_collection
from gnowsys_ndf.ndf.views.organization import *
from gnowsys_ndf.ndf.views.course import *
from gnowsys_ndf.ndf.views.person import *
from gnowsys_ndf.ndf.views.enrollment import *
from gnowsys_ndf.ndf.views.methods import get_execution_time


@get_execution_time
def mis_detail(request, group_id, app_id=None, app_set_id=None, app_set_instance_id=None, app_name=None):
    """
    custom view for custom GAPPS
    """

    auth = None
    if ObjectId.is_valid(group_id) is False :
      group_ins = node_collection.one({'_type': "Group","name": group_id})
      auth = node_collection.one({'_type': 'Author', 'name': unicode(request.user.username) })
      if group_ins:
        group_id = str(group_ins._id)
      else :
        auth = node_collection.one({'_type': 'Author', 'name': unicode(request.user.username) })
        if auth :
          group_id = str(auth._id)
    else :
      pass

    app = None
    if app_id is None:
      app = node_collection.one({'_type': "GSystemType", 'name': app_name})
      if app:
        app_id = str(app._id)
    else:
      app = node_collection.one({'_id': ObjectId(app_id)})

    app_name = app.name 

    app_collection_set = [] 
    atlist = []
    rtlist = []
    
    app_set = ""
    nodes = ""
    # nodes_dict = ""
    nodes_keys = []
    app_menu = ""
    app_set_template = ""
    app_set_instance_template = ""
    app_set_instance_name = ""
    app_set_name = ""
    title = ""
    tags = ""
    content = ""
    location = ""
    system = None
    system_id = ""
    system_type = ""
    system_mime_type = ""
    template = ""
    property_display_order = []
    events_arr = []
    university_wise_students_count = []

    template_prefix = "mis"

    if request.user.id:
      if auth is None:
        auth = node_collection.one({'_type': 'Author', 'name': unicode(request.user.username)})

      agency_type = auth.agency_type
      agency_type_node = node_collection.one({'_type': "GSystemType", 'name': agency_type}, {'collection_set': 1})
      if agency_type_node:
        for eachset in agency_type_node.collection_set:
          app_collection_set.append(node_collection.one({"_id": eachset}, {'_id': 1, 'name': 1, 'type_of': 1}))      

    # for eachset in app.collection_set:
    #   app_collection_set.append(node_collection.one({"_id":eachset}, {'_id': 1, 'name': 1, 'type_of': 1}))
      # app_set = node_collection.find_one({"_id":eachset})
      # app_collection_set.append({"id": str(app_set._id), "name": app_set.name, 'type_of'})

    if app_set_id:
      app_set = node_collection.one({'_type': "GSystemType", '_id': ObjectId(app_set_id)}, {'name': 1, 'type_of': 1})
      
      view_file_extension = ".py"
      app_set_view_file_name = ""
      app_set_view_file_path = ""

      if app_set.type_of:
        app_set_type_of = node_collection.one({'_type': "GSystemType", '_id': ObjectId(app_set.type_of[0])}, {'name': 1})

        app_set_view_file_name = app_set_type_of.name.lower().replace(" ", "_")
        # print "\n app_set_view_file_name (type_of): ", app_set_view_file_name, "\n"

      else:
        app_set_view_file_name = app_set.name.lower().replace(" ", "_")
        # print "\n app_set_view_file_name: ", app_set_view_file_name, "\n"

      app_set_view_file_path = os.path.join(os.path.dirname(__file__), app_set_view_file_name + view_file_extension)
      # print "\n app_set_view_file_path: ", app_set_view_file_path, "\n"

      if os.path.exists(app_set_view_file_path):
        # print "\n Call this function...\n"
        if app_set_view_file_name == "course":
          app_set_view_file_name = "mis_course"
        return eval(app_set_view_file_name + "_detail")(request, group_id, app_id, app_set_id, app_set_instance_id, app_name)

      # print "\n Perform fallback code...\n"

      classtype = ""
      app_set_template = "yes"
      template = "ndf/"+template_prefix+"_list.html"

      systemtype = node_collection.find_one({"_id":ObjectId(app_set_id)})
      systemtype_name = systemtype.name
      title = systemtype_name

      if request.method=="POST":
        search = request.POST.get("search","")
        classtype = request.POST.get("class","")
        nodes = list(node_collection.find({'name':{'$regex':search, '$options': 'i'},'member_of': {'$all': [systemtype._id]}}, {'name': 1}).sort('name', 1))
      else :
        nodes = list(node_collection.find({'member_of': {'$all': [systemtype._id]},'group_set':{'$all': [ObjectId(group_id)]}}, {'name': 1}).sort('name', 1))

      nodes_keys = [('name', "Name")]
      # nodes_dict = []
      # for each in nodes:
      #   nodes_dict.append({"p_id":str(each._id), "name":each.name, "created_by":User.objects.get(id=each.created_by).username, "created_at":each.created_at})
                         
    else :
      app_menu = "yes"
      template = "ndf/"+template_prefix+"_list.html"
      title = app_name

      university_gst = node_collection.one({'_type': "GSystemType", 'name': "University"})
      student_gst = node_collection.one({'_type': "GSystemType", 'name': "Student"})

      mis_admin = node_collection.one(
          {'_type': "Group", 'name': "MIS_admin"},
          {'_id': 1}
      )

      university_cur = node_collection.find(
        {'member_of': university_gst._id, 'group_set': mis_admin._id},
        {'name': 1, 'relation_set.affiliated_college': 1}
      ).sort('name', 1)

      for each_university in university_cur:
        affiliated_college_ids_list = []
        for rel in each_university.relation_set:
          if rel and "affiliated_college" in rel:
            affiliated_college_ids_list = rel["affiliated_college"]
            break

        students_cur = node_collection.find(
          {
            'member_of': student_gst._id,
            'relation_set.student_belongs_to_college': {'$in': affiliated_college_ids_list}
          }
        )

        # university_wise_students_count[each_university.name] = students_cur.count()
        university_wise_students_count.append((each_university.name, students_cur.count()))

    if app_set_instance_id :
        app_set_instance_template = "yes"
        template = "ndf/"+template_prefix+"_details.html"

        app_set_template = ""
        systemtype_attributetype_set = []
        systemtype_relationtype_set = []
        system = node_collection.find_one({"_id":ObjectId(app_set_instance_id)})
        systemtype = node_collection.find_one({"_id":ObjectId(app_set_id)})
        for each in systemtype.attribute_type_set:
            systemtype_attributetype_set.append({"type":each.name,"type_id":str(each._id),"value":each.data_type})
        for each in systemtype.relation_type_set:
            systemtype_relationtype_set.append({"rt_name":each.name,"type_id":str(each._id)})

        for eachatset in systemtype_attributetype_set :
            for eachattribute in triple_collection.find({"_type":"GAttribute", "subject":system._id, "attribute_type.$id":ObjectId(eachatset["type_id"])}):
                atlist.append({"type":eachatset["type"],"type_id":eachatset["type_id"],"value":eachattribute.object_value})
        for eachrtset in systemtype_relationtype_set :
            for eachrelation in triple_collection.find({"_type":"GRelation", "subject":system._id, "relation_type.$id":ObjectId(eachrtset["type_id"])}):
                right_subject = node_collection.find_one({"_id":ObjectId(eachrelation.right_subject)})
                rtlist.append({"type":eachrtset["rt_name"],"type_id":eachrtset["type_id"],"value_name": right_subject.name,"value_id":str(right_subject._id)})

        # To support consistent view

        property_order = system.property_order
        system.get_neighbourhood(systemtype._id)

        # array of dict for events ---------------------
                
        if system.has_key('organiser_of_event') and len(system.organiser_of_event): # gives list of events

            for event in system.organiser_of_event:
                event.get_neighbourhood(event.member_of)
                
                tempdict = {}
                tempdict['title'] = event.name
                
                if event.start_time:# and len(event.start_time) == 16:
                    # print "\n start_time: ", event.start_time, " -- ", event.start_time.strftime('%m/%d/%Y %H:%M')
                    # dt = datetime.datetime.strptime(event.start_time , '%m/%d/%Y %H:%M')
                    dt = event.start_time.strftime('%m/%d/%Y %H:%M')
                    tempdict['start'] = dt
                if event.end_time:# and len(event.end_time) == 16:
                    # print "\n end_time: ", event.end_time, " -- ", event.end_time.strftime('%m/%d/%Y %H:%M')
                    # dt = datetime.datetime.strptime(event.end_time , '%m/%d/%Y %H:%M')
                    dt = event.end_time.strftime('%m/%d/%Y %H:%M')
                    tempdict['end'] = dt
                tempdict['id'] = str(event._id)
                events_arr.append(tempdict)

        elif system.has_key('event_organised_by'): # gives list of colleges/host of events

            for host in system.event_organised_by:
                host.get_neighbourhood(host.member_of)

                tempdict = {}
                tempdict['title'] = host.name

                if system.start_time:# and len(system.start_time) == 16:
                    # dt = datetime.datetime.strptime(system.start_time , '%m/%d/%Y %H:%M')
                    dt = event.start_time.strftime('%m/%d/%Y %H:%M')
                    tempdict['start'] = dt
                if system.end_time:# and len(system.start_time) == 16:
                    # dt = datetime.datetime.strptime(system.end_time , '%m/%d/%Y %H:%M')
                    dt = event.end_time.strftime('%m/%d/%Y %H:%M')
                    tempdict['end'] = dt
                
                tempdict['id'] = str(host._id)
                events_arr.append(tempdict)

        # print json.dumps(events_arr)

        # END --- array of dict for events ---------------------

        for tab_name, fields_order in property_order:
            display_fields = []
            for field, altname in fields_order:
                if system.structure[field] == bool:
                    display_fields.append((altname, ("Yes" if system[field] else "No")))

                elif not system[field]:
                    display_fields.append((altname, system[field]))
                    continue

                elif system.structure[field] == datetime.datetime:
                    display_fields.append((altname, system[field].date()))

                elif type(system.structure[field]) == list:
                    if system[field]:
                        if type(system.structure[field][0]) == ObjectId:
                            name_list = []
                            for right_sub_dict in system[field]:
                                name_list.append(right_sub_dict.name)
                            display_fields.append((altname, ", ".join(name_list)))
                        elif system.structure[field][0] == datetime.datetime:
                            date_list = []
                            for dt in system[field]:
                                date_list.append(dt.strftime("%d/%m/%Y"))
                            display_fields.append((altname, ", ".join(date_list)))
                        else:
                            display_fields.append((altname, ", ".join(system[field])))

                else:
                    display_fields.append((altname, system[field]))

            property_display_order.append((tab_name, display_fields))

        # End of code

        tags = ",".join(system.tags)
        content = system.content
        location = system.location
        app_set_name = systemtype.name
        system_id = system._id
        system_type = system._type

        # print "\n app_set_instance_name: ", app_set_instance_name
        # print "\n app_set_name: ", app_set_name

        if system_type == 'File':
            system_mime_type = system.mime_type

        app_set_instance_name = system.name
        title =  systemtype.name +"-" +system.name



    variable = RequestContext(request, {
                                        'group_id':group_id, 'groupid':group_id, 'app_name':app_name, 'app_id':app_id,
                                        "app_collection_set":app_collection_set, "app_set_id":app_set_id, 
                                        "nodes":nodes, "nodes_keys": nodes_keys, "app_menu":app_menu, "app_set_template":app_set_template,
                                        "app_set_instance_template":app_set_instance_template, "app_set_name":app_set_name,
                                        "app_set_instance_name":app_set_instance_name, "title":title,
                                        "app_set_instance_atlist":atlist, "app_set_instance_rtlist":rtlist, 
                                        'tags':tags, 'location':location, "content":content, "system_id":system_id,
                                        "system_type":system_type,"mime_type":system_mime_type, "app_set_instance_id":app_set_instance_id,
                                        "node":system, 'group_id':group_id, "property_display_order": property_display_order,
                                        "events_arr":events_arr, 'university_wise_students_count': university_wise_students_count
                                        })

    return render_to_response(template, variable)
      
      
@login_required
@get_execution_time
def mis_create_edit(request, group_id, app_id, app_set_id=None, app_set_instance_id=None, app_name=None):
    """
    create new instance of app_set of apps view for custom GAPPS
    """
    auth = None
    if ObjectId.is_valid(group_id) is False :
      group_ins = node_collection.one({'_type': "Group","name": group_id})
      auth = node_collection.one({'_type': 'Author', 'name': unicode(request.user.username) })
      if group_ins:
        group_id = str(group_ins._id)
      else :
        auth = node_collection.one({'_type': 'Author', 'name': unicode(request.user.username) })
        if auth :
          group_id = str(auth._id)
    else :
      pass

    app = None
    if app_id is None:
      app = node_collection.one({'_type': "GSystemType", 'name': app_name})
      if app:
        app_id = str(app._id)
    else:
      app = node_collection.one({'_id': ObjectId(app_id)})

    app_name = app.name 

    # app_name = "mis"
    app_collection_set = [] 
    # app = node_collection.find_one({"_id":ObjectId(app_id)})
    app_set = ""
    app_set_instance_name = ""
    nodes = ""
    systemtype = ""
    title = ""
    tags = ""
    location=""
    content_org = ""
    system_id = ""
    system_type = ""
    system_mime_type = ""
    systemtype_name = ""
    systemtype_attributetype_set = []
    systemtype_relationtype_set = []
    title = ""
    file_st_ids = []
    app_type_of_id = ""
    File = 'False'
    obj_id_ins = ObjectId()

    template_prefix = "mis"

    user_id = int(request.user.id)  # getting django user id
    user_name = unicode(request.user.username)  # getting django user name

    if request.user.id:
      if auth is None:
        auth = node_collection.one({'_type': 'Author', 'name': unicode(request.user.username)})
      agency_type = auth.agency_type
      agency_type_node = node_collection.one({'_type': "GSystemType", 'name': agency_type}, {'collection_set': 1})
      if agency_type_node:
        for eachset in agency_type_node.collection_set:
          app_collection_set.append(node_collection.one({"_id": eachset}, {'_id': 1, 'name': 1, 'type_of': 1}))      

    # for eachset in app.collection_set:
    #   app_collection_set.append(node_collection.one({"_id":eachset}, {'_id': 1, 'name': 1, 'type_of': 1}))
      # app_set = node_collection.find_one({"_id":eachset})
      # app_collection_set.append({"id": str(app_set._id), "name": app_set.name, 'type_of'})

    if app_set_id:
        app_set = node_collection.one({'_type': "GSystemType", '_id': ObjectId(app_set_id)}, {'name': 1, 'type_of': 1})

        view_file_extension = ".py"
        app_set_view_file_name = ""
        app_set_view_file_path = ""

        if app_set.type_of:
            app_set_type_of = node_collection.one({'_type': "GSystemType", '_id': ObjectId(app_set.type_of[0])}, {'name': 1})

            app_set_view_file_name = app_set_type_of.name.lower().replace(" ", "_")
            # print "\n app_set_view_file_name (type_of): ", app_set_view_file_name, "\n"

        else:
            app_set_view_file_name = app_set.name.lower().replace(" ", "_")
            # print "\n app_set_view_file_name: ", app_set_view_file_name, "\n"

        app_set_view_file_path = os.path.join(os.path.dirname(__file__), app_set_view_file_name + view_file_extension)
        # print "\n app_set_view_file_path: ", app_set_view_file_path, "\n"

        if os.path.exists(app_set_view_file_path):
            # print "\n Call this function...\n"
            return eval(app_set_view_file_name + "_create_edit")(request, group_id, app_id, app_set_id, app_set_instance_id, app_name)


        # print "\n Perform fallback code...\n"

        systemtype = node_collection.find_one({"_id":ObjectId(app_set_id)})
        systemtype_name = systemtype.name
        title = systemtype_name + " - new"
        for each in systemtype.attribute_type_set:
            systemtype_attributetype_set.append({"type":each.name,"type_id":str(each._id),"value":each.data_type, 'sub_values': each.complex_data_type, 'altnames': each.altnames})

        for eachrt in systemtype.relation_type_set:
            # object_type = [ {"name":rtot.name, "id":str(rtot._id)} for rtot in node_collection.find({'member_of': {'$all': [ node_collection.find_one({"_id":eachrt.object_type[0]})._id]}}) ]
            object_type_cur = node_collection.find({'member_of': {'$in': eachrt.object_type}})
            object_type = []
            for each in object_type_cur:
              object_type.append({"name":each.name, "id":str(each._id)})
            systemtype_relationtype_set.append({"rt_name": eachrt.name, "type_id": str(eachrt._id), "object_type": object_type})
    
    request_at_dict = {}
    request_rt_dict = {}

    files_sts = ['File','Image','Video']
    if app_set_id:
        app = node_collection.one({'_id':ObjectId(app_set_id)})
        for each in files_sts:
            node_id = node_collection.one({'name':each,'_type':'GSystemType'})._id
            if node_id in app.type_of:
                File = 'True'

    if app_set_instance_id : # at and rt set editing instance
        system = node_collection.find_one({"_id":ObjectId(app_set_instance_id)})
        for eachatset in systemtype_attributetype_set :
            eachattribute = triple_collection.find_one({"_type":"GAttribute", "subject":system._id, "attribute_type.$id":ObjectId(eachatset["type_id"])})
            if eachattribute :
                eachatset['database_value'] = eachattribute.object_value
                eachatset['database_id'] = str(eachattribute._id)
            else :
                eachatset['database_value'] = ""
                eachatset['database_id'] = ""
        for eachrtset in systemtype_relationtype_set :
            eachrelation = triple_collection.find_one({"_type":"GRelation", "subject":system._id, "relation_type.$id":ObjectId(eachrtset["type_id"])})       
            if eachrelation:
                right_subject = node_collection.find_one({"_id":ObjectId(eachrelation.right_subject)})
                eachrtset['database_id'] = str(eachrelation._id)
                eachrtset["database_value"] = right_subject.name
                eachrtset["database_value_id"] = str(right_subject._id)
            else :
                eachrtset['database_id'] = ""
                eachrtset["database_value"] = ""
                eachrtset["database_value_id"] = ""

        tags = ",".join(system.tags)
        content_org = system.content_org
        location = system.location
        system_id = system._id
        system_type = system._type
        if system_type == 'File':
            system_mime_type = system.mime_type
        app_set_instance_name = system.name
        title =  system.name+"-"+"edit"

        
    if request.method=="POST": # post methods
        tags = request.POST.get("tags","")
        content_org = unicode(request.POST.get("content_org",""))
        name = request.POST.get("name","")
        map_geojson_data = request.POST.get('map-geojson-data') # getting markers
        user_last_visited_location = request.POST.get('last_visited_location') # getting last visited location by user
        file1 = request.FILES.get('file', '')

        for each in systemtype_attributetype_set:
            if request.POST.get(each["type_id"],"") :
                request_at_dict[each["type_id"]] = request.POST.get(each["type_id"],"")
        for eachrtset in systemtype_relationtype_set:
            if request.POST.get(eachrtset["type_id"],""):
                request_rt_dict[eachrtset["type_id"]] = request.POST.get(eachrtset["type_id"],"")
        
        if File == 'True':
            if file1:
                f = save_file(file1, name, request.user.id, group_id, content_org, tags)
                if obj_id_ins.is_valid(f):
                    newgsystem = node_collection.one({'_id':f})
                else:
                    template = "ndf/mis_list.html"
                    variable = RequestContext(request, {'group_id':group_id, 'groupid':group_id, 'app_name':app_name, 'app_id':app_id, "app_collection_set":app_collection_set, "app_set_id":app_set_id, "nodes":nodes, "systemtype_attributetype_set":systemtype_attributetype_set, "systemtype_relationtype_set":systemtype_relationtype_set, "create_new":"yes", "app_set_name":systemtype_name, 'title':title, 'File':File, 'already_uploaded_file':f})
                    return render_to_response(template, variable)
            else:
                newgsystem = node_collection.collection.File()
        else:
            newgsystem = node_collection.collection.GSystem()
        if app_set_instance_id :
            newgsystem = node_collection.find_one({"_id": ObjectId(app_set_instance_id)})

        newgsystem.name = name
        newgsystem.member_of=[ObjectId(app_set_id)]
        
        if not app_set_instance_id :
            newgsystem.created_by = request.user.id
        
        newgsystem.modified_by = request.user.id
        newgsystem.status = u"PUBLISHED"

        newgsystem.group_set.append(ObjectId(group_id))

        if tags:
             newgsystem.tags = tags.split(",")

        if content_org:
            usrname = request.user.username
            filename = slugify(newgsystem.name) + "-" + usrname
            newgsystem.content = org2html(content_org, file_prefix=filename)
            newgsystem.content_org = content_org

        # check if map markers data exist in proper format then add it into newgsystem
        if map_geojson_data:
            map_geojson_data = map_geojson_data + ","
            map_geojson_data = list(ast.literal_eval(map_geojson_data))
            newgsystem.location = map_geojson_data
            location = map_geojson_data
        else:
            map_geojson_data = []
            location = []
            newgsystem.location = map_geojson_data

        # check if user_group_location exist in proper format then add it into newgsystem
        if user_last_visited_location:
    
            user_last_visited_location = list(ast.literal_eval(user_last_visited_location))

            author = node_collection.one({'_type': "GSystemType", 'name': "Author"})
            user_group_location = node_collection.one({'_type': "Author", 'member_of': author._id, 'created_by': user_id, 'name': user_name})

            if user_group_location:
                user_group_location['visited_location'] = user_last_visited_location
                user_group_location.save()

        newgsystem.save()

        if not app_set_instance_id :
            for key,value in request_at_dict.items():
                attributetype_key = node_collection.find_one({"_id":ObjectId(key)})
                ga_node = create_gattribute(newgsystem._id, attributetype_key, value)
                # newattribute = triple_collection.collection.GAttribute()
                # newattribute.subject = newgsystem._id
                # newattribute.attribute_type = attributetype_key
                # newattribute.object_value = value
                # newattribute.save()
            for key,value in request_rt_dict.items():
                if key:
                    relationtype_key = node_collection.find_one({"_id": ObjectId(key)})
                if value:
                    right_subject = node_collection.find_one({"_id": ObjectId(value)})
                    gr_node = create_grelation(newgsystem._id, relationtype_key, right_subject._id)
                    # newrelation = triple_collection.collection.GRelation()
                    # newrelation.subject = newgsystem._id
                    # newrelation.relation_type = relationtype_key
                    # newrelation.right_subject = right_subject._id
                    # newrelation.save()

        if app_set_instance_id:
            # editing instance
            for each in systemtype_attributetype_set:
                if each["database_id"]:
                    attribute_instance = triple_collection.find_one({"_id": ObjectId(each['database_id'])})
                    attribute_instance.object_value = request.POST.get(each["database_id"],"")
                    # attribute_instance.save()
                    ga_node = create_gattribute(attribute_instance.subject, attribute_instance.attribute_type, attribute_instance.object_value)
                else :
                    if request.POST.get(each["type_id"],""):
                        attributetype_key = node_collection.find_one({"_id":ObjectId(each["type_id"])})
                        # newattribute = triple_collection.collection.GAttribute()
                        # newattribute.subject = newgsystem._id
                        # newattribute.attribute_type = attributetype_key
                        # newattribute.object_value = request.POST.get(each["type_id"],"")
                        # newattribute.save()
                        ga_node = create_gattribute(newgsystem._id, attributetype_key, request.POST.get(each["type_id"],""))

            for eachrt in systemtype_relationtype_set:
                if eachrt["database_id"]:
                    relation_instance = triple_collection.find_one({"_id":ObjectId(eachrt['database_id'])})
                    relation_instance.right_subject = ObjectId(request.POST.get(eachrt["database_id"],""))
                    # relation_instance.save()
                    gr_node = create_grelation(relation_instance.subject, relation_instance.relation_type, relation_instance.right_subject)
                else :
                    if request.POST.get(eachrt["type_id"],""):
                        relationtype_key = node_collection.find_one({"_id":ObjectId(eachrt["type_id"])})
                        right_subject = node_collection.find_one({"_id":ObjectId(request.POST.get(eachrt["type_id"],""))})
                        gr_node = create_grelation(newgsystem._id, relationtype_key, right_subject._id)
                        # newrelation = triple_collection.collection.GRelation()
                        # newrelation.subject = newgsystem._id
                        # newrelation.relation_type = relationtype_key
                        # newrelation.right_subject = right_subject._id
                        # newrelation.save()

        return HttpResponseRedirect(reverse(app_name.lower()+":"+template_prefix+'_app_detail', kwargs={'group_id': group_id, "app_id":app_id, "app_set_id":app_set_id}))
    
    template = "ndf/"+template_prefix+"_create_edit.html"
    variable = RequestContext(request, {'group_id':group_id, 'groupid':group_id, 'app_name':app_name, 'app_id':app_id, "app_collection_set":app_collection_set, "app_set_id":app_set_id, "nodes":nodes, "systemtype_attributetype_set":systemtype_attributetype_set, "systemtype_relationtype_set":systemtype_relationtype_set, "create_new":"yes", "app_set_name":systemtype_name, 'title':title, 'File':File, 'tags':tags, "content_org":content_org, "system_id":system_id,"system_type":system_type,"mime_type":system_mime_type, "app_set_instance_name":app_set_instance_name, "app_set_instance_id":app_set_instance_id, 'location':location})
    return render_to_response(template, variable)
      
@login_required
@get_execution_time
def mis_enroll(request, group_id, app_id, app_set_id=None, app_set_instance_id=None, app_name=None):
    """
    Redirects to student_enroll function of person-view.
    """
    if app_set_id:
        app_set = node_collection.one({'_type': "GSystemType", '_id': ObjectId(app_set_id)}, {'name': 1, 'type_of': 1})

        view_file_extension = ".py"
        app_set_view_file_name = ""
        app_set_view_file_path = ""

        if app_set.type_of:
            app_set_type_of = node_collection.one({'_type': "GSystemType", '_id': ObjectId(app_set.type_of[0])}, {'name': 1})
            app_set_view_file_name = app_set_type_of.name.lower().replace(" ", "_")

        else:
            app_set_view_file_name = app_set.name.lower().replace(" ", "_")

        app_set_view_file_path = os.path.join(os.path.dirname(__file__), app_set_view_file_name + view_file_extension)

        if os.path.exists(app_set_view_file_path):
            return eval(app_set_view_file_name + "_enroll")(request, group_id, app_id, app_set_id, app_set_instance_id, app_name)


    template = "ndf/student_enroll.html"
    variable = RequestContext(request, {'groupid': group_id, 
                                        'title':title, 
                                        'app_id':app_id, 'app_name': app_name, 
                                        'app_collection_set': app_collection_set, 'app_set_id': app_set_id
                                        # 'nodes':nodes, 
                                        })
    return render_to_response(template, variable)
        
