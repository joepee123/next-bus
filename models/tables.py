#########################################################################
## Define your tables below; for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################
from datetime import datetime

db.define_table('board',
             Field('board_author', db.auth_user, default=auth.user_id),
             Field('board_title'),
             Field('board_id'),
             Field('created_on', 'datetime', default=datetime.utcnow()),
            )

db.define_table('post',
             Field('post_author', db.auth_user, default=auth.user_id),
             Field('post_parent'),
             Field('post_title'),
             Field('post_content', 'text'),
             Field('created_on', 'datetime', default=datetime.utcnow()),
             Field('post_id')
            )