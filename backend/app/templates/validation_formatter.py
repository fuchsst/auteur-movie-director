"""
Validation Result Formatters

Formats validation results for different output formats (CLI, JSON, HTML).
"""

from typing import Dict, Any, List, Optional
from enum import Enum

from .validation_pipeline import ValidationResult, ValidationIssue, Severity


class OutputFormat(Enum):
    """Supported output formats"""
    CLI = "cli"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"


class ValidationResultFormatter:
    """Format validation results for different outputs"""
    
    # ANSI color codes for CLI output
    COLORS = {
        'red': '\033[91m',
        'yellow': '\033[93m',
        'green': '\033[92m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'reset': '\033[0m',
        'bold': '\033[1m'
    }
    
    # Severity icons
    ICONS = {
        Severity.CRITICAL: '🔴',
        Severity.ERROR: '❌',
        Severity.WARNING: '⚠️',
        Severity.INFO: 'ℹ️'
    }
    
    def format(self, result: ValidationResult, format_type: OutputFormat) -> Any:
        """
        Format validation result based on output type.
        
        Args:
            result: Validation result to format
            format_type: Output format type
            
        Returns:
            Formatted result (string or dict)
        """
        if format_type == OutputFormat.CLI:
            return self.format_cli(result)
        elif format_type == OutputFormat.JSON:
            return self.format_json(result)
        elif format_type == OutputFormat.HTML:
            return self.format_html(result)
        elif format_type == OutputFormat.MARKDOWN:
            return self.format_markdown(result)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def format_cli(self, result: ValidationResult, use_color: bool = True) -> str:
        """Format for CLI output with colors and icons"""
        lines = []
        
        # Header
        if result.is_valid():
            status = f"{self.COLORS['green'] if use_color else ''}✅ VALID{self.COLORS['reset'] if use_color else ''}"
        else:
            status = f"{self.COLORS['red'] if use_color else ''}❌ INVALID{self.COLORS['reset'] if use_color else ''}"
        
        lines.append(f"\n{self.COLORS['bold'] if use_color else ''}Template Validation Result{self.COLORS['reset'] if use_color else ''}")
        lines.append("=" * 50)
        
        if result.template_id:
            lines.append(f"Template: {result.template_id} v{result.version}")
        lines.append(f"Status: {status}")
        
        if result.cached:
            lines.append(f"Result: {self.COLORS['cyan'] if use_color else ''}(cached){self.COLORS['reset'] if use_color else ''}")
        
        # Summary
        summary = result.get_summary()
        if summary['critical'] > 0 or summary['errors'] > 0 or summary['warnings'] > 0:
            lines.append(f"\nSummary:")
            if summary['critical'] > 0:
                lines.append(f"  {self.COLORS['red'] if use_color else ''}Critical: {summary['critical']}{self.COLORS['reset'] if use_color else ''}")
            if summary['errors'] > 0:
                lines.append(f"  {self.COLORS['red'] if use_color else ''}Errors: {summary['errors']}{self.COLORS['reset'] if use_color else ''}")
            if summary['warnings'] > 0:
                lines.append(f"  {self.COLORS['yellow'] if use_color else ''}Warnings: {summary['warnings']}{self.COLORS['reset'] if use_color else ''}")
            if summary['info'] > 0:
                lines.append(f"  {self.COLORS['blue'] if use_color else ''}Info: {summary['info']}{self.COLORS['reset'] if use_color else ''}")
        
        # Errors
        if result.errors:
            lines.append(f"\n{self.COLORS['red'] if use_color else ''}Errors:{self.COLORS['reset'] if use_color else ''}")
            for error in result.errors:
                lines.append(self._format_issue_cli(error, use_color))
        
        # Warnings
        if result.warnings:
            lines.append(f"\n{self.COLORS['yellow'] if use_color else ''}Warnings:{self.COLORS['reset'] if use_color else ''}")
            for warning in result.warnings:
                lines.append(self._format_issue_cli(warning, use_color))
        
        # Info
        if result.info:
            lines.append(f"\n{self.COLORS['blue'] if use_color else ''}Info:{self.COLORS['reset'] if use_color else ''}")
            for info in result.info:
                lines.append(self._format_issue_cli(info, use_color))
        
        # Validation details
        lines.append(f"\n{self.COLORS['cyan'] if use_color else ''}Validation Details:{self.COLORS['reset'] if use_color else ''}")
        lines.append(f"  Stages completed: {', '.join(result.stages_completed)}")
        lines.append(f"  Duration: {result.total_duration_ms:.2f}ms")
        
        return '\n'.join(lines)
    
    def _format_issue_cli(self, issue: ValidationIssue, use_color: bool) -> str:
        """Format a single issue for CLI output"""
        icon = self.ICONS.get(issue.severity, '•')
        
        # Color based on severity
        if use_color:
            if issue.severity == Severity.CRITICAL or issue.severity == Severity.ERROR:
                color = self.COLORS['red']
            elif issue.severity == Severity.WARNING:
                color = self.COLORS['yellow']
            else:
                color = self.COLORS['blue']
        else:
            color = ''
        
        reset = self.COLORS['reset'] if use_color else ''
        
        parts = [f"  {icon} [{issue.stage}]"]
        if issue.path:
            parts.append(f"{color}{issue.path}{reset}:")
        parts.append(issue.message)
        
        line = ' '.join(parts)
        
        if issue.suggestion:
            line += f"\n     💡 {issue.suggestion}"
        
        return line
    
    def format_json(self, result: ValidationResult) -> Dict[str, Any]:
        """Format for JSON API response"""
        return result.to_dict()
    
    def format_html(self, result: ValidationResult) -> str:
        """Format as HTML for web display"""
        html_parts = []
        
        # CSS styles
        html_parts.append("""
        <style>
            .validation-result {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 20px;
            }
            .validation-header {
                border-bottom: 2px solid #ddd;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            .validation-status {
                font-size: 24px;
                font-weight: bold;
            }
            .validation-status.valid { color: #28a745; }
            .validation-status.invalid { color: #dc3545; }
            .validation-section {
                margin: 20px 0;
            }
            .validation-section h3 {
                margin-bottom: 10px;
            }
            .issue {
                margin: 10px 0;
                padding: 10px;
                border-left: 4px solid;
                background: #f8f9fa;
            }
            .issue.critical, .issue.error { 
                border-color: #dc3545; 
                background: #f8d7da;
            }
            .issue.warning { 
                border-color: #ffc107; 
                background: #fff3cd;
            }
            .issue.info { 
                border-color: #17a2b8; 
                background: #d1ecf1;
            }
            .issue-header {
                font-weight: bold;
                margin-bottom: 5px;
            }
            .issue-suggestion {
                margin-top: 5px;
                font-style: italic;
                color: #666;
            }
            .summary-table {
                border-collapse: collapse;
                margin: 10px 0;
            }
            .summary-table td {
                padding: 5px 15px;
            }
            .cached-badge {
                display: inline-block;
                background: #17a2b8;
                color: white;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 12px;
                margin-left: 10px;
            }
        </style>
        """)
        
        # Header
        html_parts.append('<div class="validation-result">')
        html_parts.append('<div class="validation-header">')
        
        status_class = 'valid' if result.is_valid() else 'invalid'
        status_text = '✅ VALID' if result.is_valid() else '❌ INVALID'
        
        html_parts.append(f'<div class="validation-status {status_class}">')
        html_parts.append(f'{status_text}')
        if result.cached:
            html_parts.append('<span class="cached-badge">Cached</span>')
        html_parts.append('</div>')
        
        if result.template_id:
            html_parts.append(f'<div>Template: <strong>{result.template_id}</strong> v{result.version}</div>')
        
        html_parts.append('</div>')
        
        # Summary
        summary = result.get_summary()
        if any(summary.values()):
            html_parts.append('<div class="validation-section">')
            html_parts.append('<h3>Summary</h3>')
            html_parts.append('<table class="summary-table">')
            
            if summary['critical'] > 0:
                html_parts.append(f'<tr><td>🔴 Critical:</td><td>{summary["critical"]}</td></tr>')
            if summary['errors'] > 0:
                html_parts.append(f'<tr><td>❌ Errors:</td><td>{summary["errors"]}</td></tr>')
            if summary['warnings'] > 0:
                html_parts.append(f'<tr><td>⚠️ Warnings:</td><td>{summary["warnings"]}</td></tr>')
            if summary['info'] > 0:
                html_parts.append(f'<tr><td>ℹ️ Info:</td><td>{summary["info"]}</td></tr>')
            
            html_parts.append('</table>')
            html_parts.append('</div>')
        
        # Issues by type
        if result.errors:
            html_parts.append('<div class="validation-section">')
            html_parts.append('<h3>Errors</h3>')
            for error in result.errors:
                html_parts.append(self._format_issue_html(error))
            html_parts.append('</div>')
        
        if result.warnings:
            html_parts.append('<div class="validation-section">')
            html_parts.append('<h3>Warnings</h3>')
            for warning in result.warnings:
                html_parts.append(self._format_issue_html(warning))
            html_parts.append('</div>')
        
        if result.info:
            html_parts.append('<div class="validation-section">')
            html_parts.append('<h3>Information</h3>')
            for info in result.info:
                html_parts.append(self._format_issue_html(info))
            html_parts.append('</div>')
        
        # Details
        html_parts.append('<div class="validation-section">')
        html_parts.append('<h3>Validation Details</h3>')
        html_parts.append(f'<div>Stages completed: {", ".join(result.stages_completed)}</div>')
        html_parts.append(f'<div>Duration: {result.total_duration_ms:.2f}ms</div>')
        html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return ''.join(html_parts)
    
    def _format_issue_html(self, issue: ValidationIssue) -> str:
        """Format a single issue for HTML output"""
        severity_class = issue.severity.value
        icon = self.ICONS.get(issue.severity, '•')
        
        html = f'<div class="issue {severity_class}">'
        html += f'<div class="issue-header">{icon} [{issue.stage}]'
        if issue.path:
            html += f' <code>{issue.path}</code>'
        html += '</div>'
        html += f'<div>{issue.message}</div>'
        
        if issue.suggestion:
            html += f'<div class="issue-suggestion">💡 {issue.suggestion}</div>'
        
        html += '</div>'
        
        return html
    
    def format_markdown(self, result: ValidationResult) -> str:
        """Format as Markdown for documentation"""
        lines = []
        
        # Header
        lines.append("# Template Validation Result\n")
        
        if result.template_id:
            lines.append(f"**Template:** `{result.template_id}` v{result.version}")
        
        if result.is_valid():
            lines.append("**Status:** ✅ VALID")
        else:
            lines.append("**Status:** ❌ INVALID")
        
        if result.cached:
            lines.append("*(Result from cache)*")
        
        lines.append("")
        
        # Summary
        summary = result.get_summary()
        if any(summary.values()):
            lines.append("## Summary\n")
            lines.append("| Type | Count |")
            lines.append("|------|-------|")
            
            if summary['critical'] > 0:
                lines.append(f"| 🔴 Critical | {summary['critical']} |")
            if summary['errors'] > 0:
                lines.append(f"| ❌ Errors | {summary['errors']} |")
            if summary['warnings'] > 0:
                lines.append(f"| ⚠️ Warnings | {summary['warnings']} |")
            if summary['info'] > 0:
                lines.append(f"| ℹ️ Info | {summary['info']} |")
            
            lines.append("")
        
        # Errors
        if result.errors:
            lines.append("## Errors\n")
            for error in result.errors:
                lines.append(self._format_issue_markdown(error))
            lines.append("")
        
        # Warnings
        if result.warnings:
            lines.append("## Warnings\n")
            for warning in result.warnings:
                lines.append(self._format_issue_markdown(warning))
            lines.append("")
        
        # Info
        if result.info:
            lines.append("## Information\n")
            for info in result.info:
                lines.append(self._format_issue_markdown(info))
            lines.append("")
        
        # Details
        lines.append("## Validation Details\n")
        lines.append(f"- **Stages completed:** {', '.join(result.stages_completed)}")
        lines.append(f"- **Duration:** {result.total_duration_ms:.2f}ms")
        
        return '\n'.join(lines)
    
    def _format_issue_markdown(self, issue: ValidationIssue) -> str:
        """Format a single issue for Markdown output"""
        icon = self.ICONS.get(issue.severity, '•')
        
        parts = [f"- {icon} **[{issue.stage}]**"]
        if issue.path:
            parts.append(f"`{issue.path}`:")
        parts.append(issue.message)
        
        line = ' '.join(parts)
        
        if issue.suggestion:
            line += f"\n  - 💡 *{issue.suggestion}*"
        
        return line
    
    def format_batch_summary(self, results: Dict[str, ValidationResult], 
                           format_type: OutputFormat = OutputFormat.CLI) -> str:
        """
        Format summary of batch validation results.
        
        Args:
            results: Dictionary mapping file paths to validation results
            format_type: Output format type
            
        Returns:
            Formatted batch summary
        """
        total_files = len(results)
        valid_files = sum(1 for r in results.values() if r.is_valid())
        invalid_files = total_files - valid_files
        
        total_errors = sum(len(r.errors) for r in results.values())
        total_warnings = sum(len(r.warnings) for r in results.values())
        
        if format_type == OutputFormat.CLI:
            lines = [
                "\n" + "=" * 60,
                f"{self.COLORS['bold']}Batch Validation Summary{self.COLORS['reset']}",
                "=" * 60,
                f"Total files: {total_files}",
                f"{self.COLORS['green']}✅ Valid: {valid_files}{self.COLORS['reset']}",
                f"{self.COLORS['red']}❌ Invalid: {invalid_files}{self.COLORS['reset']}",
                f"{self.COLORS['red']}Total errors: {total_errors}{self.COLORS['reset']}",
                f"{self.COLORS['yellow']}Total warnings: {total_warnings}{self.COLORS['reset']}",
                ""
            ]
            
            if invalid_files > 0:
                lines.append(f"{self.COLORS['red']}Invalid files:{self.COLORS['reset']}")
                for file_path, result in results.items():
                    if not result.is_valid():
                        error_count = len(result.errors)
                        lines.append(f"  ❌ {file_path} ({error_count} errors)")
            
            return '\n'.join(lines)
            
        elif format_type == OutputFormat.JSON:
            return {
                "summary": {
                    "total_files": total_files,
                    "valid_files": valid_files,
                    "invalid_files": invalid_files,
                    "total_errors": total_errors,
                    "total_warnings": total_warnings
                },
                "results": {
                    file_path: result.to_dict() 
                    for file_path, result in results.items()
                }
            }
        
        else:
            raise ValueError(f"Batch summary not supported for format: {format_type}")