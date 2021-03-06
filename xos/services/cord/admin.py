from django.contrib import admin

from services.cord.models import *
from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from django.contrib.contenttypes import generic
from suit.widgets import LinkedSelect
from core.admin import ServiceAppAdmin,SliceInline,ServiceAttrAsTabInline, ReadOnlyAwareAdmin, XOSTabularInline, ServicePrivilegeInline, TenantRootTenantInline, TenantRootPrivilegeInline
from core.middleware import get_request

from functools import update_wrapper
from django.contrib.admin.views.main import ChangeList
from django.core.urlresolvers import reverse
from django.contrib.admin.utils import quote

#-----------------------------------------------------------------------------
# vOLT
#-----------------------------------------------------------------------------

class VOLTServiceAdmin(ReadOnlyAwareAdmin):
    model = VOLTService
    verbose_name = "vOLT Service"
    verbose_name_plural = "vOLT Service"
    list_display = ("backend_status_icon", "name", "enabled")
    list_display_links = ('backend_status_icon', 'name', )
    fieldsets = [(None, {'fields': ['backend_status_text', 'name','enabled','versionNumber', 'description',"view_url","icon_url" ], 'classes':['suit-tab suit-tab-general']})]
    readonly_fields = ('backend_status_text', )
    inlines = [SliceInline,ServiceAttrAsTabInline,ServicePrivilegeInline]

    extracontext_registered_admins = True

    user_readonly_fields = ["name", "enabled", "versionNumber", "description"]

    suit_form_tabs =(('general', 'vOLT Service Details'),
        ('administration', 'Administration'),
        #('tools', 'Tools'),
        ('slices','Slices'),
        ('serviceattrs','Additional Attributes'),
        ('serviceprivileges','Privileges'),
    )

    suit_form_includes = (('voltadmin.html', 'top', 'administration'),
                           ) #('hpctools.html', 'top', 'tools') )

    def queryset(self, request):
        return VOLTService.get_service_objects_by_user(request.user)

class VOLTTenantForm(forms.ModelForm):
    s_tag = forms.CharField()
    c_tag = forms.CharField()
    creator = forms.ModelChoiceField(queryset=User.objects.all())

    def __init__(self,*args,**kwargs):
        super (VOLTTenantForm,self ).__init__(*args,**kwargs)
        self.fields['kind'].widget.attrs['readonly'] = True
        self.fields['provider_service'].queryset = VOLTService.get_service_objects().all()
        if self.instance:
            # fields for the attributes
            self.fields['c_tag'].initial = self.instance.c_tag
            self.fields['s_tag'].initial = self.instance.s_tag
            self.fields['creator'].initial = self.instance.creator
        if (not self.instance) or (not self.instance.pk):
            # default fields for an 'add' form
            self.fields['kind'].initial = VOLT_KIND
            self.fields['creator'].initial = get_request().user
            if VOLTService.get_service_objects().exists():
               self.fields["provider_service"].initial = VOLTService.get_service_objects().all()[0]

    def save(self, commit=True):
        self.instance.s_tag = self.cleaned_data.get("s_tag")
        self.instance.c_tag = self.cleaned_data.get("c_tag")
        self.instance.creator = self.cleaned_data.get("creator")
        return super(VOLTTenantForm, self).save(commit=commit)

    class Meta:
        model = VOLTTenant

class VOLTTenantAdmin(ReadOnlyAwareAdmin):
    list_display = ('backend_status_icon', 'id', 'service_specific_id', 's_tag', 'c_tag', 'subscriber_root' )
    list_display_links = ('backend_status_icon', 'id')
    fieldsets = [ (None, {'fields': ['backend_status_text', 'kind', 'provider_service', 'subscriber_root', 'service_specific_id', # 'service_specific_attribute',
                                     's_tag', 'c_tag', 'creator'],
                          'classes':['suit-tab suit-tab-general']})]
    readonly_fields = ('backend_status_text', 'service_specific_attribute')
    form = VOLTTenantForm

    suit_form_tabs = (('general','Details'),)

    def queryset(self, request):
        return VOLTTenant.get_tenant_objects_by_user(request.user)

class AccessDeviceInline(XOSTabularInline):
    model = AccessDevice
    fields = ['volt_device','uplink','vlan']
    readonly_fields = []
    extra = 0
#    max_num = 0
    suit_classes = 'suit-tab suit-tab-accessdevices'

#    @property
#    def selflink_reverse_path(self):
#        return "admin:cord_volttenant_change"

class VOLTDeviceAdmin(ReadOnlyAwareAdmin):
    list_display = ('backend_status_icon', 'name', 'openflow_id', 'driver' )
    list_display_links = ('backend_status_icon', 'name', 'openflow_id')
    fieldsets = [ (None, {'fields': ['backend_status_text','name','volt_service','openflow_id','driver','access_agent'],
                          'classes':['suit-tab suit-tab-general']})]
    readonly_fields = ('backend_status_text',)
    inlines = [AccessDeviceInline]

    suit_form_tabs = (('general','Details'), ('accessdevices','Access Devices'))

class AccessDeviceAdmin(ReadOnlyAwareAdmin):
    list_display = ('backend_status_icon', 'id', 'volt_device', 'uplink', 'vlan' )
    list_display_links = ('backend_status_icon', 'id')
    fieldsets = [ (None, {'fields': ['backend_status_text','volt_device','uplink','vlan'],
                          'classes':['suit-tab suit-tab-general']})]
    readonly_fields = ('backend_status_text',)

    suit_form_tabs = (('general','Details'),)

class AgentPortMappingInline(XOSTabularInline):
    model = AgentPortMapping
    fields = ['access_agent', 'mac', 'port']
    readonly_fields = []
    extra = 0
#    max_num = 0
    suit_classes = 'suit-tab suit-tab-accessportmaps'

#    @property
#    def selflink_reverse_path(self):
#        return "admin:cord_volttenant_change"

class AccessAgentAdmin(ReadOnlyAwareAdmin):
    list_display = ('backend_status_icon', 'name', 'mac' )
    list_display_links = ('backend_status_icon', 'name')
    fieldsets = [ (None, {'fields': ['backend_status_text','name','volt_service','mac'],
                          'classes':['suit-tab suit-tab-general']})]
    readonly_fields = ('backend_status_text',)
    inlines= [AgentPortMappingInline]

    suit_form_tabs = (('general','Details'), ('accessportmaps', 'Port Mappings'))

#-----------------------------------------------------------------------------
# vCPE
#-----------------------------------------------------------------------------

class VSGServiceForm(forms.ModelForm):
    bbs_api_hostname = forms.CharField(required=False)
    bbs_api_port = forms.IntegerField(required=False)
    bbs_server = forms.CharField(required=False)
    backend_network_label = forms.CharField(required=False)
    bbs_slice = forms.ModelChoiceField(queryset=Slice.objects.all(), required=False)
    dns_servers = forms.CharField(required=False)
    url_filter_kind = forms.ChoiceField(choices=VSGService.URL_FILTER_KIND_CHOICES, required=False)
    node_label = forms.CharField(required=False)

    def __init__(self,*args,**kwargs):
        super (VSGServiceForm,self ).__init__(*args,**kwargs)
        if self.instance:
            self.fields['bbs_api_hostname'].initial = self.instance.bbs_api_hostname
            self.fields['bbs_api_port'].initial = self.instance.bbs_api_port
            self.fields['bbs_server'].initial = self.instance.bbs_server
            self.fields['backend_network_label'].initial = self.instance.backend_network_label
            self.fields['bbs_slice'].initial = self.instance.bbs_slice
            self.fields['dns_servers'].initial = self.instance.dns_servers
            self.fields['url_filter_kind']. initial = self.instance.url_filter_kind
            self.fields['node_label'].initial = self.instance.node_label

    def save(self, commit=True):
        self.instance.bbs_api_hostname = self.cleaned_data.get("bbs_api_hostname")
        self.instance.bbs_api_port = self.cleaned_data.get("bbs_api_port")
        self.instance.bbs_server = self.cleaned_data.get("bbs_server")
        self.instance.backend_network_label = self.cleaned_data.get("backend_network_label")
        self.instance.bbs_slice = self.cleaned_data.get("bbs_slice")
        self.instance.dns_servers = self.cleaned_data.get("dns_servers")
        self.instance.url_filter_kind = self.cleaned_data.get("url_filter_kind")
        self.instance.node_label = self.cleaned_data.get("node_label")
        return super(VSGServiceForm, self).save(commit=commit)

    class Meta:
        model = VSGService

class VSGServiceAdmin(ReadOnlyAwareAdmin):
    model = VSGService
    verbose_name = "vSG Service"
    verbose_name_plural = "vSG Service"
    list_display = ("backend_status_icon", "name", "enabled")
    list_display_links = ('backend_status_icon', 'name', )
    fieldsets = [(None,             {'fields': ['backend_status_text', 'name','enabled','versionNumber', 'description', "view_url", "icon_url", "service_specific_attribute", "node_label"],
                                     'classes':['suit-tab suit-tab-general']}),
                 ("backend config", {'fields': [ "backend_network_label", "url_filter_kind", "bbs_api_hostname", "bbs_api_port", "bbs_server", "bbs_slice"],
                                     'classes':['suit-tab suit-tab-backend']}),
                 ("vSG config", {'fields': ["dns_servers"],
                                     'classes':['suit-tab suit-tab-vsg']}) ]
    readonly_fields = ('backend_status_text', "service_specific_attribute")
    inlines = [SliceInline,ServiceAttrAsTabInline,ServicePrivilegeInline]
    form = VSGServiceForm

    extracontext_registered_admins = True

    user_readonly_fields = ["name", "enabled", "versionNumber", "description"]

    suit_form_tabs =(('general', 'Service Details'),
        ('backend', 'Backend Config'),
        ('vsg', 'vSG Config'),
        ('administration', 'Administration'),
        #('tools', 'Tools'),
        ('slices','Slices'),
        ('serviceattrs','Additional Attributes'),
        ('serviceprivileges','Privileges') ,
    )

    suit_form_includes = (('vcpeadmin.html', 'top', 'administration'),
                           ) #('hpctools.html', 'top', 'tools') )

    def queryset(self, request):
        return VSGService.get_service_objects_by_user(request.user)

class VSGTenantForm(forms.ModelForm):
    bbs_account = forms.CharField(required=False)
    creator = forms.ModelChoiceField(queryset=User.objects.all())
    instance = forms.ModelChoiceField(queryset=Instance.objects.all(),required=False)
    last_ansible_hash = forms.CharField(required=False)
    wan_container_ip = forms.CharField(required=False)
    wan_container_mac = forms.CharField(required=False)

    def __init__(self,*args,**kwargs):
        super (VSGTenantForm,self ).__init__(*args,**kwargs)
        self.fields['kind'].widget.attrs['readonly'] = True
        self.fields['provider_service'].queryset = VSGService.get_service_objects().all()
        if self.instance:
            # fields for the attributes
            self.fields['bbs_account'].initial = self.instance.bbs_account
            self.fields['creator'].initial = self.instance.creator
            self.fields['instance'].initial = self.instance.instance
            self.fields['last_ansible_hash'].initial = self.instance.last_ansible_hash
            self.fields['wan_container_ip'].initial = self.instance.wan_container_ip
            self.fields['wan_container_mac'].initial = self.instance.wan_container_mac
        if (not self.instance) or (not self.instance.pk):
            # default fields for an 'add' form
            self.fields['kind'].initial = VCPE_KIND
            self.fields['creator'].initial = get_request().user
            if VSGService.get_service_objects().exists():
               self.fields["provider_service"].initial = VSGService.get_service_objects().all()[0]

    def save(self, commit=True):
        self.instance.creator = self.cleaned_data.get("creator")
        self.instance.instance = self.cleaned_data.get("instance")
        self.instance.last_ansible_hash = self.cleaned_data.get("last_ansible_hash")
        return super(VSGTenantForm, self).save(commit=commit)

    class Meta:
        model = VSGTenant

class VSGTenantAdmin(ReadOnlyAwareAdmin):
    list_display = ('backend_status_icon', 'id', 'subscriber_tenant' )
    list_display_links = ('backend_status_icon', 'id')
    fieldsets = [ (None, {'fields': ['backend_status_text', 'kind', 'provider_service', 'subscriber_tenant', 'service_specific_id', # 'service_specific_attribute',
                                     'wan_container_ip', 'wan_container_mac', 'bbs_account', 'creator', 'instance', 'last_ansible_hash'],
                          'classes':['suit-tab suit-tab-general']})]
    readonly_fields = ('backend_status_text', 'service_specific_attribute', 'bbs_account', 'wan_container_ip', 'wan_container_mac')
    form = VSGTenantForm

    suit_form_tabs = (('general','Details'),)

    def queryset(self, request):
        return VSGTenant.get_tenant_objects_by_user(request.user)

#-----------------------------------------------------------------------------
# vBNG
#-----------------------------------------------------------------------------

class VBNGServiceForm(forms.ModelForm):
    vbng_url = forms.CharField(required=False)

    def __init__(self,*args,**kwargs):
        super (VBNGServiceForm,self ).__init__(*args,**kwargs)
        if self.instance:
            self.fields['vbng_url'].initial = self.instance.vbng_url

    def save(self, commit=True):
        self.instance.vbng_url = self.cleaned_data.get("vbng_url")
        return super(VBNGServiceForm, self).save(commit=commit)

    class Meta:
        model = VBNGService

class VBNGServiceAdmin(ReadOnlyAwareAdmin):
    model = VBNGService
    verbose_name = "vBNG Service"
    verbose_name_plural = "vBNG Service"
    list_display = ("backend_status_icon", "name", "enabled")
    list_display_links = ('backend_status_icon', 'name', )
    fieldsets = [(None, {'fields': ['backend_status_text', 'name','enabled','versionNumber', 'description', "view_url", "icon_url",
                                    'vbng_url' ],
                         'classes':['suit-tab suit-tab-general']})]
    readonly_fields = ('backend_status_text', )
    inlines = [SliceInline,ServiceAttrAsTabInline,ServicePrivilegeInline]
    form = VBNGServiceForm

    extracontext_registered_admins = True

    user_readonly_fields = ["name", "enabled", "versionNumber", "description"]

    suit_form_tabs =(('general', 'vBNG Service Details'),
        ('administration', 'Administration'),
        #('tools', 'Tools'),
        ('slices','Slices'),
        ('serviceattrs','Additional Attributes'),
        ('serviceprivileges','Privileges'),
    )

    suit_form_includes = (('vbngadmin.html', 'top', 'administration'),
                           ) #('hpctools.html', 'top', 'tools') )

    def queryset(self, request):
        return VBNGService.get_service_objects_by_user(request.user)

class VBNGTenantForm(forms.ModelForm):
    routeable_subnet = forms.CharField(required=False)
    mapped_hostname = forms.CharField(required=False)
    mapped_ip = forms.CharField(required=False)
    mapped_mac =  forms.CharField(required=False)

    def __init__(self,*args,**kwargs):
        super (VBNGTenantForm,self ).__init__(*args,**kwargs)
        self.fields['kind'].widget.attrs['readonly'] = True
        self.fields['provider_service'].queryset = VBNGService.get_service_objects().all()
        if self.instance:
            # fields for the attributes
            self.fields['routeable_subnet'].initial = self.instance.routeable_subnet
            self.fields['mapped_hostname'].initial = self.instance.mapped_hostname
            self.fields['mapped_ip'].initial = self.instance.mapped_ip
            self.fields['mapped_mac'].initial = self.instance.mapped_mac
        if (not self.instance) or (not self.instance.pk):
            # default fields for an 'add' form
            self.fields['kind'].initial = VBNG_KIND
            if VBNGService.get_service_objects().exists():
               self.fields["provider_service"].initial = VBNGService.get_service_objects().all()[0]

    def save(self, commit=True):
        self.instance.routeable_subnet = self.cleaned_data.get("routeable_subnet")
        self.instance.mapped_hostname = self.cleaned_data.get("mapped_hostname")
        self.instance.mapped_ip = self.cleaned_data.get("mapped_ip")
        self.instance.mapped_mac = self.cleaned_data.get("mapped_mac")
        return super(VBNGTenantForm, self).save(commit=commit)

    class Meta:
        model = VBNGTenant

class VBNGTenantAdmin(ReadOnlyAwareAdmin):
    list_display = ('backend_status_icon', 'id', 'subscriber_tenant' )
    list_display_links = ('backend_status_icon', 'id')
    fieldsets = [ (None, {'fields': ['backend_status_text', 'kind', 'provider_service', 'subscriber_tenant', 'service_specific_id', # 'service_specific_attribute',
                                     'routeable_subnet', 'mapped_hostname', 'mapped_ip', 'mapped_mac'],
                          'classes':['suit-tab suit-tab-general']})]
    readonly_fields = ('backend_status_text', 'service_specific_attribute')
    form = VBNGTenantForm

    suit_form_tabs = (('general','Details'),)

    def queryset(self, request):
        return VBNGTenant.get_tenant_objects_by_user(request.user)

#-----------------------------------------------------------------------------
# CordSubscriberRoot
#-----------------------------------------------------------------------------

class VOLTTenantInline(XOSTabularInline):
    model = VOLTTenant
    fields = ['provider_service', 'subscriber_root', 'service_specific_id']
    readonly_fields = ['provider_service', 'subscriber_root', 'service_specific_id']
    extra = 0
    max_num = 0
    suit_classes = 'suit-tab suit-tab-volttenants'
    fk_name = 'subscriber_root'
    verbose_name = 'subscribed tenant'
    verbose_name_plural = 'subscribed tenants'

    @property
    def selflink_reverse_path(self):
        return "admin:cord_volttenant_change"

    def queryset(self, request):
        qs = super(VOLTTenantInline, self).queryset(request)
        return qs.filter(kind=VOLT_KIND)

class CordSubscriberRootForm(forms.ModelForm):
    url_filter_level = forms.CharField(required = False)
    uplink_speed = forms.CharField(required = False)
    downlink_speed = forms.CharField(required = False)
    status = forms.ChoiceField(choices=CordSubscriberRoot.status_choices, required=True)
    enable_uverse = forms.BooleanField(required=False)
    cdn_enable = forms.BooleanField(required=False)

    def __init__(self,*args,**kwargs):
        super (CordSubscriberRootForm,self ).__init__(*args,**kwargs)
        self.fields['kind'].widget.attrs['readonly'] = True
        if self.instance:
            self.fields['url_filter_level'].initial = self.instance.url_filter_level
            self.fields['uplink_speed'].initial = self.instance.uplink_speed
            self.fields['downlink_speed'].initial = self.instance.downlink_speed
            self.fields['status'].initial = self.instance.status
            self.fields['enable_uverse'].initial = self.instance.enable_uverse
            self.fields['cdn_enable'].initial = self.instance.cdn_enable
        if (not self.instance) or (not self.instance.pk):
            # default fields for an 'add' form
            self.fields['kind'].initial = CORD_SUBSCRIBER_KIND
            self.fields['uplink_speed'].initial = CordSubscriberRoot.get_default_attribute("uplink_speed")
            self.fields['downlink_speed'].initial = CordSubscriberRoot.get_default_attribute("downlink_speed")
            self.fields['status'].initial = CordSubscriberRoot.get_default_attribute("status")
            self.fields['enable_uverse'].initial = CordSubscriberRoot.get_default_attribute("enable_uverse")
            self.fields['cdn_enable'].initial = CordSubscriberRoot.get_default_attribute("cdn_enable")

    def save(self, commit=True):
        self.instance.url_filter_level = self.cleaned_data.get("url_filter_level")
        self.instance.uplink_speed = self.cleaned_data.get("uplink_speed")
        self.instance.downlink_speed = self.cleaned_data.get("downlink_speed")
        self.instance.status = self.cleaned_data.get("status")
        self.instance.enable_uverse = self.cleaned_data.get("enable_uverse")
        self.instance.cdn_enable = self.cleaned_data.get("cdn_enable")
        return super(CordSubscriberRootForm, self).save(commit=commit)

    class Meta:
        model = CordSubscriberRoot

class CordSubscriberRootAdmin(ReadOnlyAwareAdmin):
    list_display = ('backend_status_icon', 'id',  'name', )
    list_display_links = ('backend_status_icon', 'id', 'name', )
    fieldsets = [ (None, {'fields': ['backend_status_text', 'kind', 'name', 'service_specific_id', # 'service_specific_attribute',
                                     'url_filter_level', "uplink_speed", "downlink_speed", "status", "enable_uverse", "cdn_enable"],
                          'classes':['suit-tab suit-tab-general']})]
    readonly_fields = ('backend_status_text', 'service_specific_attribute',)
    form = CordSubscriberRootForm
    inlines = (VOLTTenantInline, TenantRootPrivilegeInline)

    suit_form_tabs =(('general', 'Cord Subscriber Root Details'),
        ('volttenants','VOLT Tenancy'),
        ('tenantrootprivileges','Privileges')
    )

    def queryset(self, request):
        return CordSubscriberRoot.get_tenant_objects_by_user(request.user)

admin.site.register(VOLTService, VOLTServiceAdmin)
admin.site.register(VOLTTenant, VOLTTenantAdmin)
admin.site.register(VOLTDevice, VOLTDeviceAdmin)
admin.site.register(AccessDevice, AccessDeviceAdmin)
admin.site.register(AccessAgent, AccessAgentAdmin)

admin.site.register(VSGService, VSGServiceAdmin)
admin.site.register(VSGTenant, VSGTenantAdmin)
admin.site.register(VBNGService, VBNGServiceAdmin)
admin.site.register(VBNGTenant, VBNGTenantAdmin)
admin.site.register(CordSubscriberRoot, CordSubscriberRootAdmin)

