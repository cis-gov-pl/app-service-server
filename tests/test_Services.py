# Test suite for Services module

from Services import Validator, Service, conf, ServiceStore
from Jobs import Job
from nose.tools import eq_, ok_
import os


def setup_module():
    """
    Some configuration options to adapt environment for testing
    :return:
    """
    # from Config import conf
    # change directory from which job data are loaded
    conf.gate_path_jobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assests')
    # add test service to services list
    ServiceStore['test'] = Service('test', dict(
        config={},
        sets={},
        variables=dict(
            test_float=dict(
                type="float",
                default=2.3,
                values=[0, 100]
            ),
            test_float_array=dict(
                type="float_array",
                default=[2.3,3.9],
                values=[4,0, 100]
            ),
            test_date=dict(
                type="datetime",
                default="20150115 173000",
                values="%Y%m%d %H%M%S"
            ),
            test_object=dict(
                type="object",
                default=dict(
                    A=1,
                    B=[2, 3, 4]
                ),
                values=dict(
                    A=dict(
                        type="int",
                        default=1,
                        values=[0, 1000]
                    ),
                    B=dict(
                        type="int_array",
                        default=[2, 3, 4],
                        values=[3, 0, 10000]),
                    C=dict(
                        type="datetime",
                        default="20151115 112000",
                        values="%Y%m%d %H%M%S"
                    )
                )
            ),
            test_object_array=dict(
                type="object_array",
                default=[],
                values=[10,dict(
                    K=dict(
                        type="float",
                        default=1.2,
                        values=[0, 1000]
                    ),
                    L=dict(
                        type="datetime",
                        default="20011119 103010",
                        values="%Y%m%d %H%M%S"
                    )
                )]
            )
        )
    ))
    ServiceStore['default'] = Service('test', dict(
        config={},
        sets={},
        variables = {
        "CIS_SCHEDULER" : {
            "type" : "string",
            "default" : "ssh",
            "values" : ["pbs", "ssh"]
        },
        "CIS_QUEUE" : {
            "type" : "string",
            "default" : "test_slc6",
            "values" : ["short", "long", "test_slc6"]
        },
        "CIS_SSH_HOST" : {
            "type" : "string",
            "default" : "localhost",
            "values" : ["localhost"]
        }
        }
    ))


class TestValidator:
    @classmethod
    def setup_class(cls):
        cls.valid_job = Job('test_valid_job.json')
        cls.service = ServiceStore['test']

    def test_validate(self):
        """
        Validator.validate
        :return:
        """
        # job = Job('test_valid_job.json')
        # print self.valid_job.id()
        Validator.validate(self.valid_job)
        print self.valid_job.data.data
        eq_(1, 1, "OK")

    def test_validate_value_date(self):
        """
        Validator.validate_value:  datetime variable
        :return:
        """
        var_name = 'test_date'
        # correct date input
        ok_(Validator.validate_value(var_name, '20150317 135200', self.service),
            'Proper date')
        # returns 2003-4-4 13:52 ... is that correct? lets keep it that way
        ok_(Validator.validate_value(var_name, '200344 135200', self.service),
            'Month and day without leading zeros')

        # failed date input
        ok_(not Validator.validate_value(var_name, '201503 135200', self.service),
            "Too short date")
        ok_(not Validator.validate_value(var_name, '20150344 135200', self.service),
            "Day out of bounds")
        ok_(not Validator.validate_value(var_name, '20150317 995200', self.service),
            "Hour our of bounds")
        ok_(not Validator.validate_value(var_name, '20151317 005200', self.service),
            "Month out of bound")
        ok_(not Validator.validate_value(var_name, '201w 005200', self.service),
            "Random string")

    def test_validate_value_float_array(self):
        """
        Validator.validate_value:  float_array variable
        :return:
        """
        var_name = 'test_float_array'
        # proper value
        ok_(Validator.validate_value(var_name, [0.1,55.3,2.3], self.service),
            "Basic value - array")
        ok_(Validator.validate_value(var_name, (0.1,55.3,2.3), self.service),
            "Basic value - tuple")

        # failed input
        # failed up to commit #106aa0669
        ok_(not Validator.validate_value(var_name, 0.1, self.service),
            "Number instead of array")
        ok_(not Validator.validate_value(var_name, (0.1,55.3,2.3,33.21,5.1,7.5), self.service),
            "Too many values")
        ok_(not Validator.validate_value(var_name, (599999999.1,7.5), self.service),
            "One value out of bounds")
        ok_(not Validator.validate_value(var_name, (5.1,-7.5), self.service),
            "One value out of bounds")

    def test_validate_value_float(self):
        """
        Validator.validate_value:  float variable
        :return:
        """
        var_name = 'test_float'
        # correct value
        ok_(Validator.validate_value(var_name, 0.1, self.service),
            "Proper value")
        ok_(Validator.validate_value(var_name, '0.1', self.service),
            'Float as a string')

        # failed input
        ok_(not Validator.validate_value(var_name, "ss", self.service),
            'Random string')
        # localization? Nope and lets keep it that way
        ok_(not Validator.validate_value(var_name, "0,1", self.service),
            'Localized Float')

    def test_validate_value_object(self):
        """
        Validator.validate_value:  object variable
        :return:
        """
        var_name = 'test_object'
        # proper values
        ok_(Validator.validate_value(var_name,
                                     dict(A=2,B=[4,5,34]),
                                     self.service),"Basic object")
        ok_(Validator.validate_value(var_name,{},
                                     self.service),"Empty object")

        # failed input
        ok_(not Validator.validate_value(var_name,dict(C='bla'),
                                     self.service),"Unsupported variable")
        ok_(not Validator.validate_value(var_name,[],
                                     self.service),"Array instead of dict")
        ok_(not Validator.validate_value(var_name,dict(A=99999999),
                                     self.service),"Not valid variable")
        ok_(not Validator.validate_value(var_name,dict(B=[1,2,3,4,5,4]),
                                     self.service),"Not valid variable")

        ServiceStore['test'].variables['too_nested'] = dict(
            type="object",
            default={},
            values=dict(
                T=dict(
                    type="int",
                    default=4,
                    values=[0, 12]
                ),
                nested=dict(
                    type="object",
                    default={},
                    values=dict(
                         Z=dict(
                            type="int",
                            default=3,
                            values=[0, 12]
                        )
                    )
                )
            )
        )
        ok_(not Validator.validate_value('too_nested',dict(
            T=1,
            nested=dict(
                Z=5
            )),
            self.service),"Too nested object")

    def test_validate_value_object_array(self):
        """
        Validator.validate_value:  object_array variable
        :return:
        """
        var_name = 'test_object_array'
        #proper values
        ok_(Validator.validate_value(var_name,
                                     [dict(K=2,L="21011119 133010"),
                                      dict(K=0.2,L="20050119 033010"),
                                      dict(K=20.1,L="22011116 103110")],
                                     self.service),"Basic object")
        ok_(Validator.validate_value(var_name,[{},{}],
                                     self.service),"Empty objects")
        ok_(Validator.validate_value(var_name,[{}, dict(K=2,L="21011119 133010")],
                                     self.service),"Mixed empty and full objects")

        #failed input
        ok_(not Validator.validate_value(var_name,{'ss':1},
                                     self.service),"Object instead of array")
        ok_(not Validator.validate_value(var_name,
                                     [dict(K=2,L="21011119 133010"),
                                      dict(K=0.2,L="20050119 433010"), # hour out of bounds
                                      dict(K=20.1,L="22011116 103110")],
                                     self.service),"One failed value in one object in array")

    def test_validate_value_unknown_type(self):
        """
        Validator.validate_value:  service providing unsupported variable type
        :return:
        """
        var_name = 'test_mistaken'
        # service dev has misspelled 'float' and leaves 'flaot' in service file
        ServiceStore['test'].variables[var_name] = dict(
            type="flaot",
            default=2.2,
            values=[0.0, 2.2]
        )
        # failing up to commit #106aa0669
        ok_(not Validator.validate_value(var_name, "Hack payload", self.service),
            "Service developer messed up variable type and 'hacker' noticed")