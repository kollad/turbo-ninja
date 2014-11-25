__author__ = 'kollad'


class FactoryException(Exception):
    pass


class Factory(object):
    def __init__(self):
        super(Factory, self).__init__()
        self.classes = {}

    def register(self, classname, cls=None, module=None):
        if cls is None and module is None:
            raise ValueError('No cls= or module= specified')

        if classname in self.classes:
            return

        self.classes[classname] = {
            'module': module,
            'cls': cls,
        }

    def unregister(self, *classnames):
        for classname in classnames:
            if classname in self.classes:
                self.classes.pop(classname)

    def __getattr__(self, name):
        classes = self.classes
        if name not in classes:
            if name[0] == name[0].lower():
                raise AttributeError
            raise FactoryException('Unknown class <%s>' % name)

        item = classes[name]
        cls = item['cls']
        if cls is None:
            if item['module']:
                module = __import__(name=item['module'], fromlist='.')
                if not hasattr(module, name):
                    raise FactoryException(
                        'No class named <%s> in module <%s>' % (name, item['module'])
                    )
                cls = item['cls'] = getattr(module, name)
            else:
                raise FactoryException('No module= set, cannot create class')

        return cls

    get = __getattr__