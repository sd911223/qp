# coding: utf-8
from utils import utils


class Render(object):
    def __init__(self, template_path, **kw):
        from jinja2 import Environment, FileSystemLoader

        extra = kw.pop('extra', [])
        self._env = Environment(loader=FileSystemLoader(template_path), **kw)
        self._env.globals.update(extra)
        self._env.filters['max'] = max
        self._env.filters['time_format'] = utils.format_time_by_time

    def render(self, handler, path, **kw):
        args = dict(
            request=handler.request,
            loggedin=handler.current_user,
            static_url=handler.static_url,
            normal_static=self.normal_static(handler),
            admin_static=self.admin_static(handler),
        )
        kw.update(args)

        handler.write(self._env.get_template(path).render(**kw))

    def normal_static(self, handler):
        raise NotImplementedError

    def admin_static(self, handler):
        raise NotImplementedError

    def macro(self, path):
        return self._env.get_template(path).module


class PaboBlogRender(Render):
    def __init__(self, template_path, **kw):
        super(PaboBlogRender, self).__init__(template_path, **kw)

    def normal_static(self, handler):
        return lambda p: handler.static_url('%s/%s' % ("themes/normal", p))

    def admin_static(self, handler):
        return lambda p: handler.static_url('%s/%s' % ("themes/admin", p))
