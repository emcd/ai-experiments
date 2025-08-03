# ruff: noqa

class PopulationIdentifier( metaclass = __.abc.ABCMeta ):
    ''' Abstract base class for user population identifiers. '''
    # Note: Not a Protocol class because there is no common protocol.
    #       We just want issubclass support.
    #       Functions which return identifiers should cast.


class UserIdentifier( metaclass = __.abc.ABCMeta ):
    ''' Abstract base class for user identifiers. '''
    # Note: Not a Protocol class because there is no common protocol.
    #       We just want issubclass support.
    #       Functions which return identifiers should cast.


class Possessor( __.a.Protocol ):
    ''' Representation of potential owner of location. '''
    # TODO: Immutable class and object attributes.


class Omnipopulation( Possessor ):
    ''' Representation of all possible users. '''
    # TODO: Immutable class and object attributes.


@__.a.runtime_checkable
class Population( Possesor, __.a.Protocol ):
    ''' Representation of user population which can own a location. '''
    # TODO: Immutable class and object attributes.

    @__.abc.abstractmethod
    def provide_identifier( self ) -> PopulationIdentifier:
        ''' Provides system identifier for user population. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def provide_name( self ) -> str:
        ''' Provides name or alias of system identifier for user populaton. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def provide_users( self ) -> __.AbstractIterable[ User ]:
        ''' Provides users which are members of populaton. '''
        raise NotImplementedError


@__.a.runtime_checkable
class User( Possessor, __.a.Protocol ):
    ''' Representation of user who can own a location. '''
    # TODO: Immutable class and object attributes.

    @__.abc.abstractmethod
    def provide_identifier( self ) -> UserIdentifier:
        ''' Provides system identifier for user. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def provide_name( self ) -> str:
        ''' Provides name or alias of system identifier for user. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def provide_populations( self ) -> __.AbstractIterable[ Population ]:
        ''' Provides populations of which user is a member. '''
        raise NotImplementedError


class CurrentPopulation( Population, __.a.Protocol ):
    ''' Population associated with current user. '''
    # TODO: Immutable class and object attributes.


class CurrentUser( User, __.a.Protocol ):
    ''' User associated with current process or authentication. '''
    # TODO: Immutable class and object attributes.


@__.a.runtime_checkable
class SpecificPopulation( Population, __.a.Protocol ):
    ''' Specific user population on target system. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    @__.abc.abstractmethod
    def from_identifier(
        selfclass, identifier: PopulationIdentifier
    ) -> __.a.Self:
        ''' Produces user population representation from system identifier. '''
        raise NotImplementedError

    @classmethod
    @__.abc.abstractmethod
    def from_name( selfclass, name: str ) -> __.a.Self:
        ''' Produces user population representation from name or alias. '''
        raise NotImplementedError


@__.a.runtime_checkable
class SpecificUser( User, __.a.Protocol ):
    ''' Specific user on target system. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    @__.abc.abstractmethod
    def from_identifier(
        selfclass, identifier: UserIdentifier
    ) -> __.a.Self:
        ''' Produces user representation from system identifier. '''
        raise NotImplementedError

    @classmethod
    @__.abc.abstractmethod
    def from_name( selfclass, name: str ) -> __.a.Self:
        ''' Produces user representation from name or alias. '''
        raise NotImplementedError

