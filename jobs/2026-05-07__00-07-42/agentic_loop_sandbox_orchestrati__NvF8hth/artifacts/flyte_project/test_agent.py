"""
Test script for the Flyte 2.0 Agentic Loop

This script demonstrates various usage patterns and test cases.
"""

from agent_loop_standalone import run_agent_loop_locally, save_results_to_json


def test_basic_operations():
    """Test basic mathematical operations."""
    print("\n" + "="*60)
    print("TEST: Basic Operations")
    print("="*60)
    
    instructions = [
        "add 5 and 3",
        "multiply 4 by 7",
        "divide 20 by 4",
    ]
    
    results = run_agent_loop_locally(instructions)
    return results


def test_alternative_phrasings():
    """Test alternative phrasings for operations."""
    print("\n" + "="*60)
    print("TEST: Alternative Phrasings")
    print("="*60)
    
    instructions = [
        "10 plus 15",
        "6 times 8",
        "100 divided by 5",
    ]
    
    results = run_agent_loop_locally(instructions)
    return results


def test_operator_syntax():
    """Test mathematical operator syntax."""
    print("\n" + "="*60)
    print("TEST: Operator Syntax")
    print("="*60)
    
    instructions = [
        "12 + 8",
        "5 * 4",
        "30 / 6",
    ]
    
    results = run_agent_loop_locally(instructions)
    return results


def test_decimal_numbers():
    """Test operations with decimal numbers."""
    print("\n" + "="*60)
    print("TEST: Decimal Numbers")
    print("="*60)
    
    instructions = [
        "add 3.5 and 2.5",
        "multiply 1.5 by 4",
        "divide 7.5 by 2.5",
    ]
    
    results = run_agent_loop_locally(instructions)
    return results


def test_negative_numbers():
    """Test operations with negative numbers."""
    print("\n" + "="*60)
    print("TEST: Negative Numbers")
    print("="*60)
    
    instructions = [
        "add -5 and 3",
        "multiply -4 by 7",
        "divide -20 by 4",
    ]
    
    results = run_agent_loop_locally(instructions)
    return results


def test_edge_cases():
    """Test edge cases and special scenarios."""
    print("\n" + "="*60)
    print("TEST: Edge Cases")
    print("="*60)
    
    instructions = [
        "add 0 and 0",
        "multiply 10 by 0",
        "divide 0 by 5",
        "divide 10 by 1",
    ]
    
    results = run_agent_loop_locally(instructions)
    return results


def test_invalid_instructions():
    """Test invalid instruction handling."""
    print("\n" + "="*60)
    print("TEST: Invalid Instructions")
    print("="*60)
    
    instructions = [
        "calculate the square root of 16",
        "what is the average of 5 and 10",
        "power of 2 to the 3rd",
    ]
    
    results = run_agent_loop_locally(instructions)
    return results


def run_all_tests():
    """Run all test suites."""
    print("\n" + "="*60)
    print("FLYTE 2.0 AGENTIC LOOP - TEST SUITE")
    print("="*60)
    
    all_results = {}
    
    # Run all tests
    all_results['basic'] = test_basic_operations()
    all_results['alternative'] = test_alternative_phrasings()
    all_results['operators'] = test_operator_syntax()
    all_results['decimals'] = test_decimal_numbers()
    all_results['negatives'] = test_negative_numbers()
    all_results['edge_cases'] = test_edge_cases()
    all_results['invalid'] = test_invalid_instructions()
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUITE SUMMARY")
    print("="*60)
    
    total_instructions = 0
    total_successful = 0
    
    for test_name, results in all_results.items():
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        total_instructions += total
        total_successful += successful
        print(f"{test_name:20s}: {successful}/{total} successful")
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {total_successful}/{total_instructions} successful")
    print(f"Success Rate: {total_successful/total_instructions*100:.1f}%")
    
    # Save combined results
    combined_results = {
        "summary": {
            "total_instructions": total_instructions,
            "total_successful": total_successful,
            "success_rate": f"{total_successful/total_instructions*100:.1f}%"
        },
        "tests": all_results
    }
    
    save_results_to_json(combined_results, "/home/user/flyte_project/test_results.json")
    print(f"\nCombined results saved to test_results.json")
    
    return combined_results


if __name__ == "__main__":
    # Run all tests
    results = run_all_tests()
    
    # Also save to artifacts
    import os
    artifacts_dir = "/logs/artifacts/flyte_project"
    os.makedirs(artifacts_dir, exist_ok=True)
    save_results_to_json(results, f"{artifacts_dir}/test_results.json")