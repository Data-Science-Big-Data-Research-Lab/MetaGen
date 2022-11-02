__all__ = ["domain", "solution", "DefinitionError", "DomainError", "SolutionError"]


class DefinitionError(Exception):
    """ It is raised when the type of the variable is wrong.

         **Methods that can throw this exception:**

        - :py:meth:`~pycvoa.problem.domain.Domain.define_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_categorical_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_integer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_real`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_categorical`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_layer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_categorical_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.is_defined_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_type`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_type`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_list`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_element_list`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_element_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_basic`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_basic_component`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_element_component`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_value`
        """

    def __init__(self, message):
        super().__init__(message)


class DomainError(Exception):
    """ It is raised when the type of the variable is wrong.

         **Methods that can throw this exception:**

        - :py:meth:`~pycvoa.problem.domain.Domain.define_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_categorical_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_integer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_real`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_categorical`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_layer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_categorical_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.is_defined_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_type`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_type`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_list`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_element_list`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_element_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_basic`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_basic_component`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_element_component`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_value`
        """

    def __init__(self, message):
        self.message = message


class SolutionError(Exception):
    """ It is raised when the type of the variable is wrong.

         **Methods that can throw this exception:**

        - :py:meth:`~pycvoa.problem.domain.Domain.define_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_categorical_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_integer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_real`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_categorical`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_layer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_categorical_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.is_defined_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_type`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_type`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_list`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_element_list`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_element_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_basic`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_basic_component`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_element_component`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_value`
        """

    def __init__(self, message):
        self.message = message


class ItemTypeError(Exception):
    """ It is raised when the type of the variable is wrong.

         **Methods that can throw this exception:**

        - :py:meth:`~pycvoa.problem.domain.Domain.define_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_categorical_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_integer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_real`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_categorical`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_layer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_categorical_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.is_defined_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_type`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_type`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_list`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_element_list`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_element_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_basic`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_basic_component`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_element_component`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_value`
        """

    def __init__(self, message):
        self.message = message
