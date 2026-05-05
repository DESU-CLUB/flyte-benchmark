import { createTool } from '@mastra/core/tools';
import { z } from 'zod';
import { Agent } from '@mastra/core/agent';

// Define the calculator tool
const calculatorTool = createTool({
  id: 'calculator',
  description: 'Performs basic arithmetic operations',
  inputSchema: z.object({
    a: z.number().describe('First number'),
    b: z.number().describe('Second number'),
    operation: z.enum(['add', 'subtract', 'multiply', 'divide']).describe('Operation to perform'),
  }),
  execute: async (inputData) => {
    const { a, b, operation } = inputData;
    let result: number;

    switch (operation) {
      case 'add':
        result = a + b;
        break;
      case 'subtract':
        result = a - b;
        break;
      case 'multiply':
        result = a * b;
        break;
      case 'divide':
        if (b === 0) {
          throw new Error('Division by zero is not allowed');
        }
        result = a / b;
        break;
      default:
        throw new Error(`Unknown operation: ${operation}`);
    }

    return { result };
  },
});

// Create the agent with the calculator tool
const agent = new Agent({
  id: 'calculator-agent',
  name: 'Calculator Agent',
  instructions: 'You are a helpful math assistant. Use the calculator tool to answer math questions.',
  model: {
    id: 'openai/gpt-4o-mini',
  },
  tools: {
    calculator: calculatorTool,
  },
  defaultOptions: {
    maxSteps: 10,
  },
});

// Ask the agent a math question
async function main() {
  try {
    const response = await agent.generate('What is 15 multiplied by 7?');
    
    // Write the output to output.log
    const fs = require('fs');
    fs.writeFileSync('/home/user/calculator-agent/output.log', response.text);
    
    console.log('Response written to output.log');
    console.log('Response:', response.text);
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

main();