# Project Support for AI Workbench

## Overview

Add support for named projects that contain selected files from the file system. Projects provide automatic visibility of files in conversations and streamlined file operations through tool integration.

## Core Requirements

### Project Structure

1. **Project Identity**:
   - Unique name within workbench
   - Optional description
   - Creation timestamp
   - Last modified timestamp

2. **File Organization**:
   - Hierarchical structure reflecting file system
   - Files referenced by path relative to project root
   - Support for multiple root directories
   - Preserve empty directories if explicitly included

3. **File Tracking**:
   - Track file modifications
   - Record last update timestamp
   - Track which conversation modified file
   - Optional: Track modification type (tool used)

### Tool Integration

1. **Existing Tools**:
   - Add optional `project` parameter to `write_file` and `write_pieces`
   - Project parameter accepts project name (string)
   - When project specified, file appears in next conversation turn
   - Relative paths interpreted against project root

2. **New Tools Needed**:
   - `create_project`: Create new project
   - `delete_project`: Remove project (not files)

### GUI Integration

1. **Project Selection**:
   - Dropdown menu showing available projects
   - Add button to create new project
   - Edit button to modify project settings
   - Project status indicator (local/Git-backed)

2. **Project Dialog**:
   - Project name and description fields
   - Source type selection (Local/Git)
   - For Local:
     * File picker for root directories
     * Option to add multiple roots
   - For Git:
     * Repository URL
     * Branch selection
     * Local clone location
     * Sync status indicator

3. **File Display Options**:
   - Per-file toggle for line number display
   - Default display mode setting (lines/string)
   - Visual indicator of display mode
   - Quick toggle in conversation view

### Git Integration

1. **Repository Backing**:
   - Support for Git-backed projects
   - Local clone management
   - Branch tracking
   - Sync status monitoring

2. **Operations**:
   - Auto-pull on conversation start
   - Auto-commit on file modifications
   - Manual sync controls
   - Conflict resolution handling

3. **Multi-User Support**:
   - Share projects via Git repos
   - Track which user made changes
   - Merge changes from multiple users
   - Branch management for features


### Conversation Integration

1. **Project Context**:
   - Show project files at start of conversation
   - Update file content after modifications
   - Indicate which files changed in each turn
   - Support referencing files by project-relative paths

2. **History and State**:
   - Track which conversations modified project
   - Record sequence of modifications
   - Support reverting changes (future enhancement)
   - Optional: Branch/fork projects (future enhancement)

## User Experience

### Project Management

1. **Creation and Setup**:
   ```python
   # Example of project creation
   create_project(
       name="feature-x",
       description="Implementation of Feature X",
       roots=["/path/to/source", "/path/to/tests"]
   )

   # Adding files to project
   add_to_project(
       project="feature-x",
       paths=["src/feature_x.py", "tests/test_feature_x.py"],
       filters=["*.pyc", "__pycache__"]  # Optional exclusions
   )
   ```

2. **File Operations**:
   ```python
   # Writing to project file
   write_pieces(
       location="src/feature_x.py",
       project="feature-x",  # Makes file visible in next turn
       operations=[...]
   )
   ```

### Conversation Flow

1. **Project Context**:
   ```
   Assistant: Project 'feature-x' contains:
   src/
     feature_x.py (modified in turn #3)
   tests/
     test_feature_x.py
   ```

2. **Change Tracking**:
   ```
   Assistant: Changes in last turn:
   - Modified src/feature_x.py using write_pieces
   - Added tests/new_test.py using write_file
   ```

## Technical Considerations

### Data Structure

1. **Project Record**:
   ```python
   class Project( __.immut.DataclassObject ):
       name: str
       description: str
       created_at: datetime
       modified_at: datetime
       roots: list[Path]
       files: dict[Path, FileRecord]

   class FileRecord( __.immut.DataclassObject ):
       path: Path
       last_modified: datetime
       last_conversation: int  # Conversation ID
       last_tool: str         # Tool used for modification
   ```

2. **Storage**:
   - Projects stored in workbench configuration directory
   - One file per project (TOML format)
   - File content changes tracked in VCS-like storage
   - Separate index for quick project lookup

### Tool Modifications

1. **Write Operations**:
   - Check project existence
   - Validate file is in project
   - Update project file record
   - Trigger conversation update

2. **Project Operations**:
   - Validate project names
   - Handle file system operations
   - Maintain project consistency
   - Update conversation state

## Future Enhancements

1. **Version Control**:
   - Track file history
   - Support reverting changes
   - Branch/fork projects
   - Merge changes

2. **Display Preferences**:
   ```python
   class FilePreferences( __.immut.DataclassObject ):
       show_line_numbers: bool = True  # Display as line/content dict
       default_expanded: bool = True   # Show content by default
       sync_to_git: bool = True       # For Git-backed projects
   ```

3. **Git Integration**:
   ```python
   class GitConfig( __.immut.DataclassObject ):
       repo_url: str
       branch: str
       local_path: Path
       auto_sync: bool = True
       sync_interval: int = 300  # seconds
   ```

4. **Display Controls**:
   - Toggle line numbers
   - Set default view modes
   - Configure Git sync


## Migration Path

1. **Tool Updates**:
   - Add project parameter to existing tools
   - Maintain backward compatibility
   - Phase in project awareness

2. **Conversation Updates**:
   - Add project context display
   - Integrate change tracking
   - Update history format

## Implementation Phases


1. **Phase 1 - Core Features**:
   - Project creation/deletion
   - Basic file operations
   - Simple conversation integration

2. **Phase 2 - Enhanced Tools**:
   - Project-aware write operations
   - Change tracking
   - Improved conversation display

3. **Phase 3 - Advanced Features**:
   - Version control
   - Templates
   - Cross-project features
