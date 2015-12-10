# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations


from gluon import utils as gluon_utils
import datetime
import json
import time

@auth.requires_login()
def index():
    return dict()

def about():
    return dict()

def addSchedule():
    form = SQLFORM.factory(
        Field('name'),
        Field('route'),
        Field('times'))
    if form.process().accepted:
        response.flash = 'form accepted'
        session.name = form.vars.name
        session.route = form.vars.route
        session.times = form.vars.times
        loadSchedule(session.name, session.route, session.times)
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)

def getDirection():
    startID = int(request.vars['startID'])
    endID = int(request.vars['stopID'])
    if 1<=startID<=6:
        if endID-startID<0 or endID-startID>=6:
            return response.json(dict(direction="ANTI"))
        else:
            return response.json(dict(direction="CLOCK"))
    else:
        if endID-startID>0 or startID-endID>=6:
            return response.json(dict(direction="CLOCK"))
        else:
            return response.json(dict(direction="ANTI"))

def findTimes():
    # finds the closest time in the table of bus times to the current time
    # convert current time to an integer by making time = hour*60 + minutes
    # go through each time in the table and convert it to an integer in the same way
    # find time with smallest positive difference
    startID = request.vars['startID']
    direction = request.vars['direction']
    now = str(datetime.datetime.now())[11:16]
    nowInt = timeToInt(now)
    minimumDiff = 10000
    name=db(db.stops.stop_number==startID).select(db.stops.ALL).first().name
    #pretend times gives back the times of the specific schedule we are looking for
    times=db((db.schedules.name==name) & (db.schedules.route==direction)).select(db.schedules.ALL).first().times
    end = len(times)-1
    for idx, time in enumerate(times):
        difference = timeToInt(time) - nowInt
        #if the time we look at is before the time now, go to next time
        #PROBLEM: If we are looking for bus just before midnight, this search might not work - crap.
        if difference<0:
            continue
        elif difference<minimumDiff:
            minimumDiff = difference
            closestTime = time
            index = idx
    #if no closest time found, make closest time the first time in the list
    if minimumDiff==10000:
        closestTime=times[0]
        index = 0
    if index==end:
        closestTimes = [times[index], times[0], times[1]]
    elif index == end-1:
        closestTimes = [times[index], times[index+1], times[0]]
    else:
        closestTimes = [times[index], times[index+1], times[index+2]]
    return response.json(dict(closestTimes=closestTimes))

@auth.requires_login()
def board():
    board_id = request.args(0)
    return dict(board_id=board_id)


@auth.requires_signature()
def add_board():
    if not json.loads(request.vars.board_new):
        author = db().select(db.board.board_author).first().board_author
        if author != auth.user.id:
            return "ko"
    db.board.update_or_insert((db.board.board_id == request.vars.board_id),
            board_id=request.vars.board_id,
            board_title=request.vars.board_title)
    return "ok"


def checkAuth(board_author):
    """Check if logged user is the author."""
    if board_author==auth.user.id:
        return True
    return False


@auth.requires_signature()
def load_boards():
    """Loads all boards."""
    blank_list = request.vars['blank_boards[]']
    if blank_list is None:
        blank_list = []
    elif type(blank_list) is str:
        blank_list = [blank_list]
    rows = db(~db.board.board_id.belongs(blank_list)).select(db.board.ALL, orderby=~db.board.created_on)
    d = [{'board_id':r.board_id,'board_title': r.board_title,'board_is_author': checkAuth(r.board_author)}
         for r in rows]
    return response.json(dict(board_dict=d))

@auth.requires_signature()
def load_posts():
    """Loads all messages for the board."""
    blank_list = request.vars['blank_posts[]']
    if blank_list is None:
        blank_list = []
    elif type(blank_list) is str:
        blank_list = [blank_list]
    board_id = request.vars.board_id
    board = db(db.board.board_id==board_id).select()
    if board is None:
        session.flash = T("No such board")
    rows = db((~db.post.post_id.belongs(blank_list)) & (db.post.post_parent==board_id)).select(db.post.ALL, orderby=~db.post.created_on)
    d = [{'post_id':r.post_id,'post_title': r.post_title,'post_content': r.post_content,'post_is_author': checkAuth(r.post_author)}
         for r in rows]
    return response.json(dict(post_dict=d))


@auth.requires_signature()
def add_post():
    if not json.loads(request.vars.post_new):
        author = db().select(db.post.post_author).first().post_author
        if author != auth.user.id:
            return "ko"
    db.post.update_or_insert((db.post.post_id == request.vars.post_id),
                             post_id=request.vars.post_id,
                             post_title=request.vars.post_title,
                             post_content=request.vars.post_content,
                             post_parent=request.vars.post_parent)
    return "ok"


@auth.requires_signature()
def delete_post():
    delete_list = request.vars['delete_dict[]']
    if delete_list is None:
        delete_list = []
    elif type(delete_list) is str:
        delete_list = [delete_list]
    db(db.post.post_id.belongs(delete_list)).delete()

    return 'ok'

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()

def timeToInt(time):
    return int(time[0:2])*60 + int(time[3:5])



def loadSchedule(stopName, routeDirection, times):
    timesList = []
    times = times.split(",")
    for time in times:
        minutes = str(int(time)%60)
        hours = str(((int(time)-int(minutes))/60))
        if int(hours)==0:
            hours = "00"
        elif int(hours)<10:
            hours = "0" + hours
        if int(minutes)==0:
            minutes = "00"
        elif int(minutes)<10:
            minutes = "0" + minutes
        timeStr = hours + ":" + minutes
        timesList.append(timeStr)
    db.schedules.insert(name = stopName, route = routeDirection, times = timesList)
    return dict()
