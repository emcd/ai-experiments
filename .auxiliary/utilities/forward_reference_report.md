Forward Reference Analysis Report
========================================

Summary: 30 issues found across 13 files

File: sources/aiwb/apiserver/cli.py
-----------------------------------
  Line 38: Forward reference to 'ExecuteServerCommand'
    Context: attribute in class Cli
    Annotation: __.a.Union[__.a.Annotation[__.CoreCliInspectCommand, __.tyro.conf.subcommand('inspect', prefix_name=False)], __.a.Annotation[ExecuteServerCommand, __.tyro.conf.subcommand('execute', prefix_name=False)]]
    Class 'ExecuteServerCommand' defined at line 66
    Fix: Add quotes around 'ExecuteServerCommand' or use string literal

  Line 38: Forward reference to 'ExecuteServerCommand'
    Context: variable annotation
    Annotation: __.a.Union[__.a.Annotation[__.CoreCliInspectCommand, __.tyro.conf.subcommand('inspect', prefix_name=False)], __.a.Annotation[ExecuteServerCommand, __.tyro.conf.subcommand('execute', prefix_name=False)]]
    Class 'ExecuteServerCommand' defined at line 66
    Fix: Add quotes around 'ExecuteServerCommand' or use string literal

File: sources/aiwb/apiserver/server.py
--------------------------------------
  Line 35: Forward reference to 'Control'
    Context: attribute in class Accessor
    Annotation: Control
    Class 'Control' defined at line 40
    Fix: Add quotes around 'Control' or use string literal

  Line 35: Forward reference to 'Control'
    Context: variable annotation
    Annotation: Control
    Class 'Control' defined at line 40
    Fix: Add quotes around 'Control' or use string literal

File: sources/aiwb/invocables/ensembles/probability/__init__.py
---------------------------------------------------------------
  Line 36: Forward reference to 'Ensemble'
    Context: return type of function prepare
    Annotation: Ensemble
    Class 'Ensemble' defined at line 46
    Fix: Add quotes around 'Ensemble' or use string literal

File: sources/aiwb/invocables/ensembles/summarization/__init__.py
-----------------------------------------------------------------
  Line 36: Forward reference to 'Ensemble'
    Context: return type of function prepare
    Annotation: Ensemble
    Class 'Ensemble' defined at line 46
    Fix: Add quotes around 'Ensemble' or use string literal

File: sources/aiwb/invocables/ensembles/io/__init__.py
------------------------------------------------------
  Line 44: Forward reference to 'Ensemble'
    Context: return type of function prepare
    Annotation: Ensemble
    Class 'Ensemble' defined at line 56
    Fix: Add quotes around 'Ensemble' or use string literal

File: sources/aiwb/appcore/cli.py
---------------------------------
  Line 37: Forward reference to 'ConfigurationModifiers'
    Context: attribute in class Cli
    Annotation: ConfigurationModifiers
    Class 'ConfigurationModifiers' defined at line 74
    Fix: Add quotes around 'ConfigurationModifiers' or use string literal

  Line 37: Forward reference to 'ConfigurationModifiers'
    Context: variable annotation
    Annotation: ConfigurationModifiers
    Class 'ConfigurationModifiers' defined at line 74
    Fix: Add quotes around 'ConfigurationModifiers' or use string literal

File: sources/aiwb/gui/cli.py
-----------------------------
  Line 38: Forward reference to 'ExecuteServerCommand'
    Context: attribute in class Cli
    Annotation: __.a.Union[__.a.Annotation[__.CoreCliInspectCommand, __.tyro.conf.subcommand('inspect', prefix_name=False)], __.a.Annotation[ExecuteServerCommand, __.tyro.conf.subcommand('execute', prefix_name=False)]]
    Class 'ExecuteServerCommand' defined at line 66
    Fix: Add quotes around 'ExecuteServerCommand' or use string literal

  Line 38: Forward reference to 'ExecuteServerCommand'
    Context: variable annotation
    Annotation: __.a.Union[__.a.Annotation[__.CoreCliInspectCommand, __.tyro.conf.subcommand('inspect', prefix_name=False)], __.a.Annotation[ExecuteServerCommand, __.tyro.conf.subcommand('execute', prefix_name=False)]]
    Class 'ExecuteServerCommand' defined at line 66
    Fix: Add quotes around 'ExecuteServerCommand' or use string literal

File: sources/aiwb/providers/clients/openai/clients.py
------------------------------------------------------
  Line 52: Forward reference to 'Provider'
    Context: parameter 'provider' in function produce_client
    Annotation: Provider
    Class 'Provider' defined at line 149
    Fix: Add quotes around 'Provider' or use string literal

  Line 52: Forward reference to 'Client'
    Context: return type of function produce_client
    Annotation: Client
    Class 'Client' defined at line 67
    Fix: Add quotes around 'Client' or use string literal

File: sources/aiwb/providers/clients/anthropic/clients.py
---------------------------------------------------------
  Line 53: Forward reference to 'Provider'
    Context: parameter 'provider' in function produce_client
    Annotation: Provider
    Class 'Provider' defined at line 162
    Fix: Add quotes around 'Provider' or use string literal

  Line 53: Forward reference to 'Client'
    Context: return type of function produce_client
    Annotation: Client
    Class 'Client' defined at line 68
    Fix: Add quotes around 'Client' or use string literal

File: sources/aiwb/providers/clients/anthropic/conversers.py
------------------------------------------------------------
  Line 214: Forward reference to 'SerdeProcessor'
    Context: return type of function serde_processor
    Annotation: SerdeProcessor
    Class 'SerdeProcessor' defined at line 241
    Fix: Add quotes around 'SerdeProcessor' or use string literal

  Line 218: Forward reference to 'Tokenizer'
    Context: return type of function tokenizer
    Annotation: Tokenizer
    Class 'Tokenizer' defined at line 265
    Fix: Add quotes around 'Tokenizer' or use string literal

File: sources/aiwb/messages/core.py
-----------------------------------
  Line 133: Forward reference to 'Canister'
    Context: parameter 'canister' in function from_canister
    Annotation: Canister
    Class 'Canister' defined at line 149
    Fix: Add quotes around 'Canister' or use string literal

  Line 138: Forward reference to 'Canister'
    Context: return type of function produce_canister
    Annotation: Canister
    Class 'Canister' defined at line 149
    Fix: Add quotes around 'Canister' or use string literal

File: sources/aiwb/libcore/cli.py
---------------------------------
  Line 47: Forward reference to 'ConsoleDisplay'
    Context: attribute in class Cli
    Annotation: ConsoleDisplay
    Class 'ConsoleDisplay' defined at line 107
    Fix: Add quotes around 'ConsoleDisplay' or use string literal

  Line 49: Forward reference to 'InspectCommand'
    Context: attribute in class Cli
    Annotation: __.a.Union[__.a.Annotation[InspectCommand, __.tyro.conf.subcommand('inspect', prefix_name=False)], __.a.Annotation[LocationCommand, __.tyro.conf.subcommand('location', prefix_name=False)]]
    Class 'InspectCommand' defined at line 190
    Fix: Add quotes around 'InspectCommand' or use string literal

  Line 49: Forward reference to 'LocationCommand'
    Context: attribute in class Cli
    Annotation: __.a.Union[__.a.Annotation[InspectCommand, __.tyro.conf.subcommand('inspect', prefix_name=False)], __.a.Annotation[LocationCommand, __.tyro.conf.subcommand('location', prefix_name=False)]]
    Class 'LocationCommand' defined at line 215
    Fix: Add quotes around 'LocationCommand' or use string literal

  Line 47: Forward reference to 'ConsoleDisplay'
    Context: variable annotation
    Annotation: ConsoleDisplay
    Class 'ConsoleDisplay' defined at line 107
    Fix: Add quotes around 'ConsoleDisplay' or use string literal

  Line 49: Forward reference to 'InspectCommand'
    Context: variable annotation
    Annotation: __.a.Union[__.a.Annotation[InspectCommand, __.tyro.conf.subcommand('inspect', prefix_name=False)], __.a.Annotation[LocationCommand, __.tyro.conf.subcommand('location', prefix_name=False)]]
    Class 'InspectCommand' defined at line 190
    Fix: Add quotes around 'InspectCommand' or use string literal

  Line 49: Forward reference to 'LocationCommand'
    Context: variable annotation
    Annotation: __.a.Union[__.a.Annotation[InspectCommand, __.tyro.conf.subcommand('inspect', prefix_name=False)], __.a.Annotation[LocationCommand, __.tyro.conf.subcommand('location', prefix_name=False)]]
    Class 'LocationCommand' defined at line 215
    Fix: Add quotes around 'LocationCommand' or use string literal

  Line 218: Forward reference to 'LocationSurveyDirectoryCommand'
    Context: attribute in class LocationCommand
    Annotation: __.a.Union[__.a.Annotation[LocationSurveyDirectoryCommand, __.tyro.conf.subcommand('list-folder', prefix_name=False)], __.a.Annotation[LocationAcquireContentCommand, __.tyro.conf.subcommand('read', prefix_name=False)]]
    Class 'LocationSurveyDirectoryCommand' defined at line 238
    Fix: Add quotes around 'LocationSurveyDirectoryCommand' or use string literal

  Line 218: Forward reference to 'LocationAcquireContentCommand'
    Context: attribute in class LocationCommand
    Annotation: __.a.Union[__.a.Annotation[LocationSurveyDirectoryCommand, __.tyro.conf.subcommand('list-folder', prefix_name=False)], __.a.Annotation[LocationAcquireContentCommand, __.tyro.conf.subcommand('read', prefix_name=False)]]
    Class 'LocationAcquireContentCommand' defined at line 269
    Fix: Add quotes around 'LocationAcquireContentCommand' or use string literal

  Line 218: Forward reference to 'LocationSurveyDirectoryCommand'
    Context: variable annotation
    Annotation: __.a.Union[__.a.Annotation[LocationSurveyDirectoryCommand, __.tyro.conf.subcommand('list-folder', prefix_name=False)], __.a.Annotation[LocationAcquireContentCommand, __.tyro.conf.subcommand('read', prefix_name=False)]]
    Class 'LocationSurveyDirectoryCommand' defined at line 238
    Fix: Add quotes around 'LocationSurveyDirectoryCommand' or use string literal

  Line 218: Forward reference to 'LocationAcquireContentCommand'
    Context: variable annotation
    Annotation: __.a.Union[__.a.Annotation[LocationSurveyDirectoryCommand, __.tyro.conf.subcommand('list-folder', prefix_name=False)], __.a.Annotation[LocationAcquireContentCommand, __.tyro.conf.subcommand('read', prefix_name=False)]]
    Class 'LocationAcquireContentCommand' defined at line 269
    Fix: Add quotes around 'LocationAcquireContentCommand' or use string literal

File: sources/aiwb/libcore/locations/caches/simple.py
-----------------------------------------------------
  Line 46: Forward reference to '_Common'
    Context: parameter 'cache' in function invoker
    Annotation: _Common
    Class '_Common' defined at line 53
    Fix: Add quotes around '_Common' or use string literal
