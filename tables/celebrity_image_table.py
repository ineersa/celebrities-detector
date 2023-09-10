from flask import url_for, request
from flask_table import Table, Col, LinkCol


class ImageCol(Col):
    def td_contents(self, item, attr):
        image_path = getattr(item, attr[0])
        page = request.args.get('page', 1, type=int)
        if image_path:
            return f'<img src="{image_path}" alt="Image" style="max-width: 300px;">'
        else:
            return f'''
            <a href="{url_for('celebrity_image.extract', id=item.id, page=page)}">Extract face</a>
            '''


class DeleteLinkCol(Col):
    def td_contents(self, item, attr):
        _id = getattr(item, attr[0])
        page = request.args.get('page', 1, type=int)
        return f'''
            <form method="POST" action="{url_for('celebrity_image.delete', id=_id, page=page)}" style="display: inline;">
                <button type="submit" onclick='return confirm("Are you sure you want to delete?");' class="btn btn-danger btn-sm">Delete</button>
            </form>
        '''


class CelebrityImageTable(Table):
    classes = ['table', 'table-striped', 'table-bordered', 'table-hover']
    id = Col('ID')
    image_path = ImageCol('Image')
    face_image_path = ImageCol('Face Image')
    created_at = Col('Created At')
    actions = DeleteLinkCol('Actions', attr='id')

