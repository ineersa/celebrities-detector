from flask import url_for
from flask_table import Table, Col
from markupsafe import Markup


class LinkCol(Col):
    def td_format(self, content):
        return Markup('<a href="/celebrity/{}/images">Images</a>'.format(content))


class DeleteLinkCol(Col):
    def td_contents(self, item, attr):
        _id = getattr(item, attr[0])
        return f'''
            <form method="POST" action="{url_for('celebrity.delete', id=_id)}" style="display: inline;">
                <button type="submit" onclick='return confirm("Are you sure you want to delete?");' class="btn btn-danger btn-sm">Delete</button>
            </form>
        '''

class CelebrityTable(Table):
    classes = ['table', 'table-striped', 'table-bordered', 'table-hover']
    id = Col('ID')
    name = Col('Name')
    created_at = Col('Created At')
    images_link = LinkCol('Images Link', attr='id')
    actions = DeleteLinkCol('Actions', attr='id')