"""
Advanced Workflow Orchestrator for the Coder Agent

This module provides sophisticated workflow management for complex coding tasks
that require multiple AI-driven operations in sequence.
"""
import asyncio
import json
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime

from .coder_agent import CoderAgent, AgentResponse, TaskType


class WorkflowStatus(Enum):
    """Status of workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class StepType(Enum):
    """Types of workflow steps."""
    AGENT_TASK = "agent_task"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"
    LOOP = "loop"
    HUMAN_INPUT = "human_input"
    FILE_OPERATION = "file_operation"
    VALIDATION = "validation"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    step_id: str
    step_type: StepType
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Workflow:
    """Represents a complete workflow."""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowOrchestrator:
    """
    Advanced workflow orchestrator for complex coding tasks.
    
    This orchestrator can handle multi-step workflows involving:
    - Sequential and parallel task execution
    - Conditional branching
    - Human input requirements
    - File operations
    - Validation steps
    - Error handling and retries
    """
    
    def __init__(self, coder_agent: CoderAgent):
        """Initialize the workflow orchestrator."""
        self.coder_agent = coder_agent
        self.workflows: Dict[str, Workflow] = {}
        self.step_handlers = {
            StepType.AGENT_TASK: self._execute_agent_task,
            StepType.CONDITIONAL: self._execute_conditional,
            StepType.PARALLEL: self._execute_parallel,
            StepType.LOOP: self._execute_loop,
            StepType.HUMAN_INPUT: self._execute_human_input,
            StepType.FILE_OPERATION: self._execute_file_operation,
            StepType.VALIDATION: self._execute_validation,
        }
    
    def create_workflow(self, name: str, description: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new workflow and return its ID."""
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            metadata=metadata or {}
        )
        self.workflows[workflow_id] = workflow
        return workflow_id
    
    def add_step(self, workflow_id: str, step: WorkflowStep) -> bool:
        """Add a step to a workflow."""
        if workflow_id not in self.workflows:
            return False
        
        self.workflows[workflow_id].steps.append(step)
        return True
    
    def create_predefined_workflow(self, workflow_type: str, parameters: Dict[str, Any]) -> str:
        """Create a predefined workflow based on type."""
        if workflow_type == "feature_development":
            return self._create_feature_development_workflow(parameters)
        elif workflow_type == "bug_investigation":
            return self._create_bug_investigation_workflow(parameters)
        elif workflow_type == "code_review_process":
            return self._create_code_review_workflow(parameters)
        elif workflow_type == "refactoring_task":
            return self._create_refactoring_workflow(parameters)
        elif workflow_type == "project_setup":
            return self._create_project_setup_workflow(parameters)
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
    
    def _create_feature_development_workflow(self, params: Dict[str, Any]) -> str:
        """Create a comprehensive feature development workflow."""
        feature_name = params.get("feature_name", "new_feature")
        description = params.get("description", "")
        
        workflow_id = self.create_workflow(
            f"Feature Development: {feature_name}",
            f"Complete workflow for developing feature: {description}"
        )
        
        # Step 1: Analyze requirements
        self.add_step(workflow_id, WorkflowStep(
            step_id="analyze_requirements",
            step_type=StepType.AGENT_TASK,
            name="Analyze Requirements",
            description="Break down feature requirements and plan implementation",
            parameters={
                "request": f"Analyze the requirements for feature '{feature_name}': {description}. "
                          "Break it down into components, identify dependencies, and suggest implementation approach.",
                "task_type": "analysis"
            }
        ))
        
        # Step 2: Search existing codebase
        self.add_step(workflow_id, WorkflowStep(
            step_id="search_codebase",
            step_type=StepType.AGENT_TASK,
            name="Search Existing Code",
            description="Search for relevant existing code and patterns",
            parameters={
                "request": f"Search the codebase for existing patterns, functions, or classes "
                          f"that might be relevant for implementing '{feature_name}'",
                "task_type": "analysis"
            },
            dependencies=["analyze_requirements"]
        ))
        
        # Step 3: Generate code structure
        self.add_step(workflow_id, WorkflowStep(
            step_id="generate_structure",
            step_type=StepType.AGENT_TASK,
            name="Generate Code Structure",
            description="Generate the basic code structure for the feature",
            parameters={
                "request": f"Generate the code structure for feature '{feature_name}' including classes, "
                          "functions, and file organization",
                "task_type": "code_generation"
            },
            dependencies=["search_codebase"]
        ))
        
        # Step 4: Implement core functionality
        self.add_step(workflow_id, WorkflowStep(
            step_id="implement_core",
            step_type=StepType.AGENT_TASK,
            name="Implement Core Functionality",
            description="Implement the main logic of the feature",
            parameters={
                "request": f"Implement the core functionality for '{feature_name}' based on the structure",
                "task_type": "code_generation"
            },
            dependencies=["generate_structure"]
        ))
        
        # Step 5: Generate tests
        self.add_step(workflow_id, WorkflowStep(
            step_id="generate_tests",
            step_type=StepType.AGENT_TASK,
            name="Generate Tests",
            description="Create comprehensive tests for the feature",
            parameters={
                "request": f"Generate unit tests for the '{feature_name}' feature",
                "task_type": "testing"
            },
            dependencies=["implement_core"]
        ))
        
        # Step 6: Review implementation
        self.add_step(workflow_id, WorkflowStep(
            step_id="review_code",
            step_type=StepType.AGENT_TASK,
            name="Code Review",
            description="Review the implemented code for quality and best practices",
            parameters={
                "request": f"Review the implementation of '{feature_name}' for code quality, "
                          "security, performance, and best practices",
                "task_type": "code_review"
            },
            dependencies=["generate_tests"]
        ))
        
        # Step 7: Generate documentation
        self.add_step(workflow_id, WorkflowStep(
            step_id="generate_docs",
            step_type=StepType.AGENT_TASK,
            name="Generate Documentation",
            description="Create documentation for the new feature",
            parameters={
                "request": f"Generate comprehensive documentation for the '{feature_name}' feature",
                "task_type": "documentation"
            },
            dependencies=["review_code"]
        ))
        
        return workflow_id
    
    def _create_bug_investigation_workflow(self, params: Dict[str, Any]) -> str:
        """Create a bug investigation and fixing workflow."""
        bug_description = params.get("bug_description", "")
        error_message = params.get("error_message", "")
        
        workflow_id = self.create_workflow(
            "Bug Investigation",
            f"Investigate and fix bug: {bug_description}"
        )
        
        # Step 1: Analyze the bug report
        self.add_step(workflow_id, WorkflowStep(
            step_id="analyze_bug",
            step_type=StepType.AGENT_TASK,
            name="Analyze Bug Report",
            description="Analyze the bug description and error messages",
            parameters={
                "request": f"Analyze this bug report: {bug_description}. Error: {error_message}. "
                          "Identify potential causes and areas to investigate.",
                "task_type": "analysis"
            }
        ))
        
        # Step 2: Search for related code
        self.add_step(workflow_id, WorkflowStep(
            step_id="search_related_code",
            step_type=StepType.AGENT_TASK,
            name="Find Related Code",
            description="Search for code related to the bug",
            parameters={
                "request": f"Search the codebase for files and functions related to: {bug_description}",
                "task_type": "analysis"
            },
            dependencies=["analyze_bug"]
        ))
        
        # Step 3: Debug the code
        self.add_step(workflow_id, WorkflowStep(
            step_id="debug_code",
            step_type=StepType.AGENT_TASK,
            name="Debug Code",
            description="Debug the identified code to find the root cause",
            parameters={
                "request": f"Debug the code to find the root cause of: {bug_description}",
                "task_type": "bug_fixing",
                "error_message": error_message
            },
            dependencies=["search_related_code"]
        ))
        
        # Step 4: Implement fix
        self.add_step(workflow_id, WorkflowStep(
            step_id="implement_fix",
            step_type=StepType.AGENT_TASK,
            name="Implement Fix",
            description="Implement the bug fix",
            parameters={
                "request": f"Implement a fix for the bug: {bug_description}",
                "task_type": "bug_fixing"
            },
            dependencies=["debug_code"]
        ))
        
        # Step 5: Generate tests to prevent regression
        self.add_step(workflow_id, WorkflowStep(
            step_id="create_regression_tests",
            step_type=StepType.AGENT_TASK,
            name="Create Regression Tests",
            description="Create tests to prevent this bug from happening again",
            parameters={
                "request": f"Create tests to prevent regression of bug: {bug_description}",
                "task_type": "testing"
            },
            dependencies=["implement_fix"]
        ))
        
        return workflow_id
    
    def _create_code_review_workflow(self, params: Dict[str, Any]) -> str:
        """Create a comprehensive code review workflow."""
        target_files = params.get("files", [])
        focus_areas = params.get("focus_areas", ["security", "performance", "maintainability"])
        
        workflow_id = self.create_workflow(
            "Comprehensive Code Review",
            f"Review files: {', '.join(target_files)}"
        )
        
        # Step 1: Static analysis
        self.add_step(workflow_id, WorkflowStep(
            step_id="static_analysis",
            step_type=StepType.AGENT_TASK,
            name="Static Code Analysis",
            description="Perform static analysis of the code",
            parameters={
                "request": f"Perform static analysis on files: {', '.join(target_files)}",
                "task_type": "analysis"
            }
        ))
        
        # Step 2: Security review
        self.add_step(workflow_id, WorkflowStep(
            step_id="security_review",
            step_type=StepType.AGENT_TASK,
            name="Security Review",
            description="Review code for security vulnerabilities",
            parameters={
                "request": f"Review security aspects of files: {', '.join(target_files)}",
                "task_type": "code_review",
                "focus_areas": ["security"]
            },
            dependencies=["static_analysis"]
        ))
        
        # Step 3: Performance review
        self.add_step(workflow_id, WorkflowStep(
            step_id="performance_review",
            step_type=StepType.AGENT_TASK,
            name="Performance Review",
            description="Review code for performance issues",
            parameters={
                "request": f"Review performance aspects of files: {', '.join(target_files)}",
                "task_type": "code_review",
                "focus_areas": ["performance"]
            },
            dependencies=["static_analysis"]
        ))
        
        # Step 4: Generate improvement suggestions
        self.add_step(workflow_id, WorkflowStep(
            step_id="improvement_suggestions",
            step_type=StepType.AGENT_TASK,
            name="Generate Improvements",
            description="Generate specific improvement suggestions",
            parameters={
                "request": f"Generate specific improvement suggestions for: {', '.join(target_files)}",
                "task_type": "refactoring"
            },
            dependencies=["security_review", "performance_review"]
        ))
        
        return workflow_id
    
    def _create_refactoring_workflow(self, params: Dict[str, Any]) -> str:
        """Create a refactoring workflow."""
        target_files = params.get("files", [])
        goals = params.get("goals", ["readability", "maintainability", "performance"])
        
        workflow_id = self.create_workflow(
            "Code Refactoring",
            f"Refactor files for: {', '.join(goals)}"
        )
        
        # Add refactoring steps...
        # (Implementation similar to other workflows)
        
        return workflow_id
    
    def _create_project_setup_workflow(self, params: Dict[str, Any]) -> str:
        """Create a project setup workflow."""
        project_type = params.get("project_type", "python")
        features = params.get("features", [])
        
        workflow_id = self.create_workflow(
            "Project Setup",
            f"Set up {project_type} project with features: {', '.join(features)}"
        )
        
        # Add setup steps...
        # (Implementation for project initialization)
        
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str, 
                             progress_callback: Optional[Callable] = None) -> bool:
        """Execute a workflow asynchronously."""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        
        try:
            # Build dependency graph
            step_dependencies = self._build_dependency_graph(workflow.steps)
            executed_steps = set()
            
            while len(executed_steps) < len(workflow.steps):
                # Find steps ready to execute
                ready_steps = [
                    step for step in workflow.steps
                    if (step.step_id not in executed_steps and
                        all(dep in executed_steps for dep in step.dependencies))
                ]
                
                if not ready_steps:
                    # Check for circular dependencies or other issues
                    remaining_steps = [s for s in workflow.steps if s.step_id not in executed_steps]
                    raise Exception(f"Cannot progress workflow. Remaining steps: {[s.step_id for s in remaining_steps]}")
                
                # Execute ready steps (can be parallel)
                tasks = []
                for step in ready_steps:
                    tasks.append(self._execute_step(workflow, step))
                
                # Wait for all ready steps to complete
                step_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for step, result in zip(ready_steps, step_results):
                    if isinstance(result, Exception):
                        step.status = WorkflowStatus.FAILED
                        step.error = str(result)
                        if step.retry_count < step.max_retries:
                            step.retry_count += 1
                            step.status = WorkflowStatus.PENDING
                            continue
                        else:
                            workflow.status = WorkflowStatus.FAILED
                            return False
                    else:
                        step.status = WorkflowStatus.COMPLETED
                        step.result = result
                        step.completed_at = datetime.now()
                        executed_steps.add(step.step_id)
                    
                    # Call progress callback
                    if progress_callback:
                        progress_callback(workflow, step)
            
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            return True
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            return False
    
    async def _execute_step(self, workflow: Workflow, step: WorkflowStep) -> Any:
        """Execute a single workflow step."""
        step.status = WorkflowStatus.RUNNING
        step.started_at = datetime.now()
        
        handler = self.step_handlers.get(step.step_type)
        if not handler:
            raise ValueError(f"No handler for step type: {step.step_type}")
        
        # Apply timeout if specified
        if step.timeout_seconds:
            result = await asyncio.wait_for(
                handler(workflow, step),
                timeout=step.timeout_seconds
            )
        else:
            result = await handler(workflow, step)
        
        return result
    
    async def _execute_agent_task(self, workflow: Workflow, step: WorkflowStep) -> Any:
        """Execute an agent task step."""
        request = step.parameters.get("request", "")
        context = step.parameters.get("context", {})
        
        # Add workflow context to the request context
        context.update(workflow.context)
        
        response = await self.coder_agent.process_natural_language_request(request, context)
        
        if not response.success:
            raise Exception(f"Agent task failed: {response.message}")
        
        # Update workflow context with results
        if response.data:
            workflow.context.update({f"{step.step_id}_result": response.data})
        
        return response
    
    async def _execute_conditional(self, workflow: Workflow, step: WorkflowStep) -> Any:
        """Execute a conditional step."""
        condition = step.parameters.get("condition", "")
        # Implement condition evaluation logic
        # This could use the LLM to evaluate conditions based on context
        return True
    
    async def _execute_parallel(self, workflow: Workflow, step: WorkflowStep) -> Any:
        """Execute parallel sub-steps."""
        sub_steps = step.parameters.get("sub_steps", [])
        tasks = []
        for sub_step_data in sub_steps:
            # Convert sub_step_data to WorkflowStep if it's a dict
            if isinstance(sub_step_data, dict):
                sub_step = WorkflowStep(**sub_step_data)
            else:
                sub_step = sub_step_data
            tasks.append(self._execute_step(workflow, sub_step))
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def _execute_loop(self, workflow: Workflow, step: WorkflowStep) -> Any:
        """Execute a loop step."""
        iterations = step.parameters.get("iterations", 1)
        sub_step_data = step.parameters.get("sub_step")
        
        if not sub_step_data:
            return []
        
        # Convert sub_step_data to WorkflowStep if it's a dict
        if isinstance(sub_step_data, dict):
            sub_step = WorkflowStep(**sub_step_data)
        else:
            sub_step = sub_step_data
        
        results = []
        for i in range(iterations):
            result = await self._execute_step(workflow, sub_step)
            results.append(result)
        
        return results
    
    async def _execute_human_input(self, workflow: Workflow, step: WorkflowStep) -> Any:
        """Execute a human input step."""
        prompt = step.parameters.get("prompt", "Input required")
        print(f"\n🤔 Human Input Required: {prompt}")
        user_input = input("Your input: ")
        return user_input
    
    async def _execute_file_operation(self, workflow: Workflow, step: WorkflowStep) -> Any:
        """Execute a file operation step."""
        operation = step.parameters.get("operation", "read")
        file_path = step.parameters.get("file_path", "")
        
        if operation == "read":
            with open(file_path, 'r') as f:
                return f.read()
        elif operation == "write":
            content = step.parameters.get("content", "")
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        
        return None
    
    async def _execute_validation(self, workflow: Workflow, step: WorkflowStep) -> Any:
        """Execute a validation step."""
        validation_type = step.parameters.get("type", "syntax")
        target = step.parameters.get("target", "")
        
        # Implement various validation types
        # Could use the agent to validate code, syntax, etc.
        return True
    
    def _build_dependency_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """Build a dependency graph for the workflow steps."""
        graph = {}
        for step in steps:
            graph[step.step_id] = step.dependencies
        return graph
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow."""
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        
        step_statuses = []
        for step in workflow.steps:
            step_statuses.append({
                "step_id": step.step_id,
                "name": step.name,
                "status": step.status.value,
                "started_at": step.started_at,
                "completed_at": step.completed_at,
                "error": step.error
            })
        
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "created_at": workflow.created_at,
            "started_at": workflow.started_at,
            "completed_at": workflow.completed_at,
            "steps": step_statuses,
            "context": workflow.context
        }
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows with their basic information."""
        workflows = []
        for workflow in self.workflows.values():
            workflows.append({
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "status": workflow.status.value,
                "step_count": len(workflow.steps),
                "created_at": workflow.created_at
            })
        return workflows
