"""
Basic Calculator Operations Module

This module provides fundamental arithmetic operations including addition,
subtraction, multiplication, and division with proper error handling.
"""

from typing import Union

Number = Union[int, float]


class CalculatorError(Exception):
    """Custom exception for calculator operations."""
    pass


class BasicCalculator:
    """
    A calculator class providing basic arithmetic operations.
    
    This class implements the four fundamental arithmetic operations:
    addition, subtraction, multiplication, and division.
    """
    
    def __init__(self):
        """Initialize the basic calculator."""
        self.last_result = 0
        self.operation_history = []
    
    def add(self, a: Number, b: Number) -> Number:
        """
        Add two numbers together.
        
        Args:
            a (Number): First number
            b (Number): Second number
            
        Returns:
            Number: Sum of a and b
            
        Example:
            >>> calc = BasicCalculator()
            >>> calc.add(5, 3)
            8
        """
        result = a + b
        self._record_operation("add", a, b, result)
        return result
    
    def subtract(self, a: Number, b: Number) -> Number:
        """
        Subtract the second number from the first number.
        
        Args:
            a (Number): Number to subtract from
            b (Number): Number to subtract
            
        Returns:
            Number: Difference of a and b
            
        Example:
            >>> calc = BasicCalculator()
            >>> calc.subtract(10, 3)
            7
        """
        result = a - b
        self._record_operation("subtract", a, b, result)
        return result
    
    def multiply(self, a: Number, b: Number) -> Number:
        """
        Multiply two numbers together.
        
        Args:
            a (Number): First number
            b (Number): Second number
            
        Returns:
            Number: Product of a and b
            
        Example:
            >>> calc = BasicCalculator()
            >>> calc.multiply(4, 5)
            20
        """
        result = a * b
        self._record_operation("multiply", a, b, result)
        return result
    
    def divide(self, a: Number, b: Number) -> Number:
        """
        Divide the first number by the second number.
        
        Args:
            a (Number): Dividend
            b (Number): Divisor
            
        Returns:
            Number: Quotient of a divided by b
            
        Raises:
            CalculatorError: If division by zero is attempted
            
        Example:
            >>> calc = BasicCalculator()
            >>> calc.divide(15, 3)
            5.0
        """
        if b == 0:
            raise CalculatorError("Division by zero is not allowed")
        
        result = a / b
        self._record_operation("divide", a, b, result)
        return result
    
    def _record_operation(self, operation: str, a: Number, b: Number, result: Number) -> None:
        """
        Record the operation in history for later reference.
        
        Args:
            operation (str): Name of the operation
            a (Number): First operand
            b (Number): Second operand
            result (Number): Result of the operation
        """
        self.last_result = result
        self.operation_history.append({
            "operation": operation,
            "operands": [a, b],
            "result": result
        })
    
    def get_history(self) -> list:
        """
        Get the history of all operations performed.
        
        Returns:
            list: List of operation records
        """
        return self.operation_history.copy()
    
    def clear_history(self) -> None:
        """Clear the operation history."""
        self.operation_history.clear()
        self.last_result = 0
    
    def get_last_result(self) -> Number:
        """
        Get the result of the last operation.
        
        Returns:
            Number: Last calculation result
        """
        return self.last_result
