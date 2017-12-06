from lcc import models
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template

from xhtml2pdf import pisa


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        response = HttpResponse(
            result.getvalue(),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = 'inline; filename=list_people.pdf'
        return response
    return None


def generate_code(model, instance):
    if instance.parent:
        codes = [ob.code for ob in instance.parent.children.all() if ob]
        # if parent classification has children the increment
        # the last childen's code
        if codes:
            codes.sort(key=lambda x: [int(y) for y in x.split('.')])
            parts = codes[-1].split('.')
            parent_code = '.'.join(parts[:-1])
            last_code = parts[-1]
            code = '{0}.{1}'.format(parent_code, int(last_code) + 1)
        else:
            code = '{0}.1'.format(instance.parent.code)
    else:
        codes = [ob.code for ob in model.objects.filter(parent=None).all()]
        # if empty classification table - reinitialize code values
        if len(codes) == 0:
            codes = ['0']

        codes.sort(key=lambda x: [int(y) for y in x.split('.')])
        last_code = codes[-1]
        code = '{0}'.format(int(last_code) + 1)

    return code


# @TODO change for edit
def set_order(classification, parent=None):
    if parent:
        last_children = parent.get_children().last()
        if last_children:
            return last_children.order + 1
        else:
            return 1

    last_question = models.Question.objects.filter(
        parent=None, classification=classification).last()

    if last_question:
        return last_question.order + 1
    else:
        return 1
