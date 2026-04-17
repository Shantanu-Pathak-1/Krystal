"""
Project Context Plugin for Krystal AI
Scans project structure and reads files to understand coding patterns and conventions.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import logging
import re

logger = logging.getLogger("Krystal.project_context")

# File extensions to analyze by language
LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "javascript": [".js", ".jsx"],
    "typescript": [".ts", ".tsx"],
    "react": [".jsx", ".tsx"],
    "html": [".html", ".htm"],
    "css": [".css", ".scss", ".sass"],
    "json": [".json"],
    "markdown": [".md"],
}

# Directories to ignore when scanning
IGNORE_DIRECTORIES = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".vscode",
    ".idea",
    "target",
    "bin",
    "obj",
}

# Files to ignore
IGNORE_FILES = {
    ".gitignore",
    ".DS_Store",
    "package-lock.json",
    "yarn.lock",
    "requirements.txt",
}

class ProjectContext:
    """Analyzes project structure and extracts coding patterns."""
    
    def __init__(self, project_path: str):
        """
        Initialize ProjectContext with project path.
        
        Args:
            project_path: Root directory of the project
        """
        self.project_path = Path(project_path).resolve()
        self.structure: Dict[str, Any] = {}
        self.imports: Dict[str, List[str]] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self.conventions: Dict[str, Any] = {}
        
    def scan_project(self, recursive: bool = True) -> Dict[str, Any]:
        """
        Scan the project structure.
        
        Args:
            recursive: Scan subdirectories recursively
            
        Returns:
            Project structure tree
        """
        try:
            structure = self._build_tree(self.project_path, recursive)
            self.structure = structure
            logger.info(f"[ProjectContext] Scanned project: {self.project_path}")
            return structure
        except Exception as e:
            logger.error(f"[ProjectContext] Error scanning project: {e}")
            return {"error": str(e)}
    
    def _build_tree(self, path: Path, recursive: bool) -> Dict[str, Any]:
        """Build directory tree structure."""
        try:
            if not path.exists():
                return {"error": "Path does not exist"}
            
            tree = {
                "name": path.name,
                "path": str(path),
                "type": "directory" if path.is_dir() else "file",
                "children": [] if path.is_dir() else None,
                "extension": path.suffix if path.is_file() else None,
                "size": path.stat().st_size if path.is_file() else 0
            }
            
            if path.is_dir() and recursive:
                for item in sorted(path.iterdir()):
                    # Skip ignored directories
                    if item.is_dir() and item.name in IGNORE_DIRECTORIES:
                        continue
                    
                    # Skip ignored files
                    if item.is_file() and item.name in IGNORE_FILES:
                        continue
                    
                    tree["children"].append(self._build_tree(item, recursive))
            
            return tree
        except PermissionError:
            logger.warning(f"[ProjectContext] Permission denied: {path}")
            return {"name": path.name, "type": "error", "error": "Permission denied"}
        except Exception as e:
            logger.error(f"[ProjectContext] Error building tree: {e}")
            return {"name": path.name, "type": "error", "error": str(e)}
    
    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """
        Analyze a specific file to extract imports and patterns.
        
        Args:
            filepath: Path to the file
            
        Returns:
            File analysis results
        """
        try:
            file_path = Path(filepath).resolve()
            
            if not file_path.exists():
                return {"error": "File does not exist"}
            
            if not file_path.is_file():
                return {"error": "Path is not a file"}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                "path": str(file_path),
                "extension": file_path.suffix,
                "size": len(content),
                "language": self._detect_language(file_path.suffix),
                "imports": self._extract_imports(content, file_path.suffix),
                "exports": self._extract_exports(content, file_path.suffix),
                "functions": self._extract_functions(content, file_path.suffix),
                "classes": self._extract_classes(content, file_path.suffix),
                "lines": len(content.split('\n'))
            }
            
            return analysis
        except Exception as e:
            logger.error(f"[ProjectContext] Error analyzing file: {e}")
            return {"error": str(e)}
    
    def _detect_language(self, extension: str) -> str:
        """Detect programming language from file extension."""
        for lang, exts in LANGUAGE_EXTENSIONS.items():
            if extension in exts:
                return lang
        return "unknown"
    
    def _extract_imports(self, content: str, extension: str) -> List[str]:
        """Extract import statements based on file type."""
        imports = []
        
        if extension in [".py"]:
            # Python imports
            patterns = [
                r'^import\s+(\S+)',
                r'^from\s+(\S+)\s+import',
            ]
            for pattern in patterns:
                imports.extend(re.findall(pattern, content, re.MULTILINE))
        
        elif extension in [".js", ".jsx", ".ts", ".tsx"]:
            # JavaScript/TypeScript imports
            patterns = [
                r'^import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
                r'^require\([\'"]([^\'"]+)[\'"]\)',
            ]
            for pattern in patterns:
                imports.extend(re.findall(pattern, content, re.MULTILINE))
        
        return imports
    
    def _extract_exports(self, content: str, extension: str) -> List[str]:
        """Extract export statements."""
        exports = []
        
        if extension in [".js", ".jsx", ".ts", ".tsx"]:
            # JavaScript/TypeScript exports
            patterns = [
                r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)',
                r'export\s*\{\s*([^}]+)\s*\}',
            ]
            for pattern in patterns:
                exports.extend(re.findall(pattern, content, re.MULTILINE))
        
        elif extension in [".py"]:
            # Python doesn't have explicit exports, but we can look for __all__
            match = re.search(r'__all__\s*=\s*\[([^\]]+)\]', content)
            if match:
                exports = [item.strip().strip('"\'') for item in match.group(1).split(',')]
        
        return exports
    
    def _extract_functions(self, content: str, extension: str) -> List[str]:
        """Extract function names."""
        functions = []
        
        if extension in [".py"]:
            # Python functions
            functions = re.findall(r'def\s+(\w+)\s*\(', content)
        
        elif extension in [".js", ".jsx", ".ts", ".tsx"]:
            # JavaScript/TypeScript functions
            patterns = [
                r'function\s+(\w+)\s*\(',
                r'const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',
                r'(\w+)\s*:\s*function',
            ]
            for pattern in patterns:
                functions.extend(re.findall(pattern, content))
        
        return functions
    
    def _extract_classes(self, content: str, extension: str) -> List[str]:
        """Extract class names."""
        classes = []
        
        if extension in [".py"]:
            # Python classes
            classes = re.findall(r'class\s+(\w+)', content)
        
        elif extension in [".js", ".jsx", ".ts", ".tsx"]:
            # JavaScript/TypeScript classes
            classes = re.findall(r'class\s+(\w+)', content)
        
        return classes
    
    def get_relevant_files(self, query: str, max_files: int = 5) -> List[Dict[str, Any]]:
        """
        Find files relevant to a query based on filename and content.
        
        Args:
            query: Search query
            max_files: Maximum number of files to return
            
        Returns:
            List of relevant files with their paths and relevance scores
        """
        relevant_files = []
        query_lower = query.lower()
        
        try:
            for file_path in self.project_path.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # Skip ignored files
                if file_path.name in IGNORE_FILES:
                    continue
                
                # Skip ignored directories
                if any(part in IGNORE_DIRECTORIES for part in file_path.parts):
                    continue
                
                # Check filename relevance
                filename_score = 0
                for word in query_lower.split():
                    if word in file_path.name.lower():
                        filename_score += 1
                
                # Check content relevance (for text files)
                content_score = 0
                try:
                    if file_path.suffix in [".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".txt"]:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            for word in query_lower.split():
                                content_score += content.lower().count(word)
                except Exception:
                    pass
                
                total_score = filename_score * 2 + content_score
                
                if total_score > 0:
                    relevant_files.append({
                        "path": str(file_path),
                        "filename": file_path.name,
                        "score": total_score,
                        "filename_score": filename_score,
                        "content_score": content_score
                    })
            
            # Sort by score and return top files
            relevant_files.sort(key=lambda x: x["score"], reverse=True)
            return relevant_files[:max_files]
            
        except Exception as e:
            logger.error(f"[ProjectContext] Error finding relevant files: {e}")
            return []
    
    def get_project_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the project.
        
        Returns:
            Project summary including languages, file counts, etc.
        """
        try:
            summary = {
                "path": str(self.project_path),
                "name": self.project_path.name,
                "total_files": 0,
                "total_directories": 0,
                "languages": {},
                "file_types": {},
                "dependencies": {}
            }
            
            for item in self.project_path.rglob("*"):
                # Skip ignored directories
                if any(part in IGNORE_DIRECTORIES for part in item.parts):
                    continue
                
                if item.is_dir():
                    summary["total_directories"] += 1
                elif item.is_file():
                    summary["total_files"] += 1
                    
                    # Track file types
                    ext = item.suffix or "no_extension"
                    summary["file_types"][ext] = summary["file_types"].get(ext, 0) + 1
                    
                    # Track languages
                    lang = self._detect_language(item.suffix)
                    if lang != "unknown":
                        summary["languages"][lang] = summary["languages"].get(lang, 0) + 1
            
            # Extract dependencies from package.json if it exists
            package_json = self.project_path / "package.json"
            if package_json.exists():
                try:
                    import json
                    with open(package_json, 'r') as f:
                        package_data = json.load(f)
                        summary["dependencies"] = {
                            **package_data.get("dependencies", {}),
                            **package_data.get("devDependencies", {})
                        }
                except Exception:
                    pass
            
            # Extract dependencies from requirements.txt if it exists
            requirements_txt = self.project_path / "requirements.txt"
            if requirements_txt.exists():
                try:
                    with open(requirements_txt, 'r') as f:
                        deps = []
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                deps.append(line.split("==")[0].split(">=")[0].split("<=")[0])
                        summary["dependencies"]["python"] = deps
                except Exception:
                    pass
            
            return summary
            
        except Exception as e:
            logger.error(f"[ProjectContext] Error getting project summary: {e}")
            return {"error": str(e)}


# Global instance (configured later)
_project_context = None

def get_project_context(project_path: str) -> ProjectContext:
    """Get a ProjectContext instance."""
    return ProjectContext(project_path)
