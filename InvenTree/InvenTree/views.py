# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.template.loader import render_to_string
from django.http import JsonResponse

from django.views import View
from django.views.generic import UpdateView, CreateView, DeleteView
from django.views.generic.base import TemplateView

from rest_framework import views


class TreeSerializer(views.APIView):

    def itemToJson(self, item):

        data = {
            'text': item.name,
            'href': item.get_absolute_url(),
        }

        if item.has_children:
            nodes = []

            for child in item.children.all().order_by('name'):
                nodes.append(self.itemToJson(child))

            data['nodes'] = nodes

        return data

    def get(self, request, *args, **kwargs):

        top_items = self.model.objects.filter(parent=None).order_by('name')

        nodes = []

        for item in top_items:
            nodes.append(self.itemToJson(item))

        top = {
            'text': self.title,
            'nodes': nodes,
        }

        response = {
            'tree': [top]
        }

        return JsonResponse(response, safe=False)


class AjaxMixin(object):

    ajax_form_action = ''
    ajax_form_title = ''

    def get_data(self):
        return {}

    def getAjaxTemplate(self):
        if hasattr(self, 'ajax_template_name'):
            return self.ajax_template_name
        else:
            return self.template_name

    def renderJsonResponse(self, request, form=None, data={}, context={}):

        if form:
            context['form'] = form

        data['title'] = self.ajax_form_title

        data['html_form'] = render_to_string(
            self.getAjaxTemplate(),
            context,
            request=request
        )

        # Custom feedback`data
        fb = self.get_data()

        for key in fb.keys():
            data[key] = fb[key]

        return JsonResponse(data, safe=False)


class AjaxView(AjaxMixin, View):
    """ Bare-bones AjaxView """

    # By default, point to the modal_form template
    # (this can be overridden by a child class)
    ajax_template_name = 'modal_form.html'

    def post(self, request, *args, **kwargs):
        return JsonResponse('', safe=False)

    def get(self, request, *args, **kwargs):

        return self.renderJsonResponse(request)


class AjaxCreateView(AjaxMixin, CreateView):

    """ An 'AJAXified' CreateView for creating a new object in the db
    - Returns a form in JSON format (for delivery to a modal window)
    - Handles form validation via AJAX POST requests
    """

    def get(self, request, *args, **kwargs):

        response = super(CreateView, self).get(request, *args, **kwargs)

        if request.is_ajax():
            # Initialize a a new form
            form = self.form_class(initial=self.get_initial())

            return self.renderJsonResponse(request, form)

        else:
            return response

    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST, files=request.FILES)

        if request.is_ajax():

            data = {
                'form_valid': form.is_valid(),
            }

            if form.is_valid():
                obj = form.save()

                # Return the PK of the newly-created object
                data['pk'] = obj.pk

                data['url'] = obj.get_absolute_url()

            return self.renderJsonResponse(request, form, data)

        else:
            return super(CreateView, self).post(request, *args, **kwargs)




class AjaxUpdateView(AjaxMixin, UpdateView):

    """ An 'AJAXified' UpdateView for updating an object in the db
    - Returns form in JSON format (for delivery to a modal window)
    - Handles repeated form validation (via AJAX) until the form is valid
    """

    def get(self, request, *args, **kwargs):

        html_response = super(UpdateView, self).get(request, *args, **kwargs)

        if request.is_ajax():
            form = self.form_class(instance=self.get_object())

            return self.renderJsonResponse(request, form)

        else:
            return html_response

    def post(self, request, *args, **kwargs):

        form = self.form_class(instance=self.get_object(), data=request.POST, files=request.FILES)

        if request.is_ajax():

            data = {'form_valid': form.is_valid()}

            if form.is_valid():
                obj = form.save()

                data['pk'] = obj.id
                data['url'] = obj.get_absolute_url()

            response = self.renderJsonResponse(request, form, data)
            return response

        else:
            return super(UpdateView, self).post(request, *args, **kwargs)




class AjaxDeleteView(AjaxMixin, DeleteView):

    """ An 'AJAXified DeleteView for removing an object from the DB
    - Returns a HTML object (not a form!) in JSON format (for delivery to a modal window)
    - Handles deletion 
    """

    def get(self, request, *args, **kwargs):

        html_response = super(DeleteView, self).get(request, *args, **kwargs)

        if request.is_ajax():

            data = {'id': self.get_object().id,
                    'delete': False,
                    'title': self.ajax_form_title,
                    'html_data': render_to_string(self.getAjaxTemplate(),
                                                  self.get_context_data(),
                                                  request=request)
                    }

            return JsonResponse(data)

        else:
            return html_response

    def post(self, request, *args, **kwargs):

        if request.is_ajax():

            obj = self.get_object()
            pk = obj.id
            obj.delete()

            data = {'id': pk,
                    'delete': True}

            return self.renderJsonResponse(request, data=data)

        else:
            return super(DeleteView, self).post(request, *args, **kwargs)


class IndexView(TemplateView):

    template_name = 'InvenTree/index.html'


class SearchView(TemplateView):

    template_name = 'InvenTree/search.html'

    def post(self, request, *args, **kwargs):

        context = self.get_context_data()

        return super(TemplateView, self).render_to_response(context)
