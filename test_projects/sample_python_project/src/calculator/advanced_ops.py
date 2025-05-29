"""
Advanced Calculator Operations Module

This module provides advanced mathematical operations including power, square root,
logarithms, and trigonometric functions.
"""

import math
from typing import Union, Optional

Number = Union[int, float]


class AdvancedCalculatorError(Exception):
    """Custom exception for advanced calculator operations."""
    pass


class AdvancedCalculator:
    """
    Advanced calculator providing complex mathematical operations.
    
    This class extends basic arithmetic with advanced mathematical functions
    including power operations, roots, logarithms, and trigonometric functions.
    """
    
    def __init__(self):
        """Initialize the advanced calculator."""
        self.precision = 10  # Default decimal precision
        self.angle_mode = "radians"  # Default angle mode for trig functions
    
    def power(self, base: Number, exponent: Number) -> Number:
        """
        Calculate base raised to the power of exponent.
        
        Args:
            base (Number): Base number
            exponent (Number): Exponent
            
        Returns:
            Number: Result of base^exponent
            
        Example:
            >>> calc = AdvancedCalculator()
            >>> calc.power(2, 3)
            8
        """
        try:
            result = base ** exponent
            return round(result, self.precision)
        except OverflowError:
            raise AdvancedCalculatorError("Result too large to calculate")
        except Exception as e:
            raise AdvancedCalculatorError(f"Power calculation error: {e}")
    
    def square_root(self, number: Number) -> Number:
        """
        Calculate the square root of a number.
        
        Args:
            number (Number): Number to find square root of
            
        Returns:
            Number: Square root of the number
            
        Raises:
            AdvancedCalculatorError: If number is negative
            
        Example:
            >>> calc = AdvancedCalculator()
            >>> calc.square_root(16)
            4.0
        """
        if number < 0:
            raise AdvancedCalculatorError("Cannot calculate square root of negative number")
        
        result = math.sqrt(number)
        return round(result, self.precision)
    
    def nth_root(self, number: Number, n: Number) -> Number:
        """
        Calculate the nth root of a number.
        
        Args:
            number (Number): Number to find root of
            n (Number): Root degree
            
        Returns:
            Number: nth root of the number
            
        Example:
            >>> calc = AdvancedCalculator()
            >>> calc.nth_root(27, 3)
            3.0
        """
        if n == 0:
            raise AdvancedCalculatorError("Root degree cannot be zero")
        
        try:
            result = number ** (1 / n)
            return round(result, self.precision)
        except Exception as e:
            raise AdvancedCalculatorError(f"Root calculation error: {e}")
    
    def logarithm(self, number: Number, base: Optional[Number] = None) -> Number:
        """
        Calculate logarithm of a number.
        
        Args:
            number (Number): Number to find logarithm of
            base (Optional[Number]): Logarithm base (defaults to natural log)
            
        Returns:
            Number: Logarithm result
            
        Raises:
            AdvancedCalculatorError: If number is not positive
            
        Example:
            >>> calc = AdvancedCalculator()
            >>> calc.logarithm(100, 10)
            2.0
        """
        if number <= 0:
            raise AdvancedCalculatorError("Logarithm undefined for non-positive numbers")
        
        try:
            if base is None:
                result = math.log(number)  # Natural logarithm
            elif base <= 0 or base == 1:
                raise AdvancedCalculatorError("Invalid logarithm base")
            else:
                result = math.log(number, base)
            
            return round(result, self.precision)
        except Exception as e:
            raise AdvancedCalculatorError(f"Logarithm calculation error: {e}")
    
    def sine(self, angle: Number) -> Number:
        """
        Calculate sine of an angle.
        
        Args:
            angle (Number): Angle in radians or degrees (based on angle_mode)
            
        Returns:
            Number: Sine of the angle
        """
        if self.angle_mode == "degrees":
            angle = math.radians(angle)
        
        result = math.sin(angle)
        return round(result, self.precision)
    
    def cosine(self, angle: Number) -> Number:
        """
        Calculate cosine of an angle.
        
        Args:
            angle (Number): Angle in radians or degrees (based on angle_mode)
            
        Returns:
            Number: Cosine of the angle
        """
        if self.angle_mode == "degrees":
            angle = math.radians(angle)
        
        result = math.cos(angle)
        return round(result, self.precision)
    
    def tangent(self, angle: Number) -> Number:
        """
        Calculate tangent of an angle.
        
        Args:
            angle (Number): Angle in radians or degrees (based on angle_mode)
            
        Returns:
            Number: Tangent of the angle
        """
        if self.angle_mode == "degrees":
            angle = math.radians(angle)
        
        result = math.tan(angle)
        return round(result, self.precision)
    
    def factorial(self, n: int) -> int:
        """
        Calculate factorial of a non-negative integer.
        
        Args:
            n (int): Non-negative integer
            
        Returns:
            int: Factorial of n
            
        Raises:
            AdvancedCalculatorError: If n is negative or not an integer
            
        Example:
            >>> calc = AdvancedCalculator()
            >>> calc.factorial(5)
            120
        """
        if not isinstance(n, int) or n < 0:
            raise AdvancedCalculatorError("Factorial is only defined for non-negative integers")
        
        return math.factorial(n)
    
    def set_precision(self, precision: int) -> None:
        """
        Set the decimal precision for calculations.
        
        Args:
            precision (int): Number of decimal places
        """
        if precision < 0:
            raise AdvancedCalculatorError("Precision must be non-negative")
        self.precision = precision
    
    def set_angle_mode(self, mode: str) -> None:
        """
        Set the angle mode for trigonometric functions.
        
        Args:
            mode (str): Either "radians" or "degrees"
        """
        if mode not in ["radians", "degrees"]:
            raise AdvancedCalculatorError("Angle mode must be 'radians' or 'degrees'")
        self.angle_mode = mode
