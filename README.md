# Single-Cycle RV32I Processor Simulator in Python

A comprehensive RISC-V 32-bit processor simulator implementing the base integer instruction set (RV32I). This project simulates a single-cycle processor architecture where each instruction is executed in a single clock cycle.

## Overview

This simulator models a **single-cycle RISC-V processor** based on the RV32I specification. It includes:
- Complete RV32I instruction set support
- 32-bit register file (x0-x31)
- Configurable memory system
- Cycle-accurate execution
- Comprehensive instruction decoding and execution

## Features

### Supported Instruction Types

#### R-Type (Register-Register Operations)
- **ADD** - Add two registers
- **SUB** - Subtract registers
- **SLL** - Shift left logical
- **SLT** - Set less than
- **SLTU** - Set less than unsigned
- **XOR** - Bitwise XOR
- **SRL** - Shift right logical
- **SRA** - Shift right arithmetic
- **OR** - Bitwise OR
- **AND** - Bitwise AND

#### I-Type (Immediate Operations)
- **ADDI** - Add immediate
- **SLTI** - Set less than immediate
- **SLTIU** - Set less than immediate unsigned
- **XORI** - XOR immediate
- **ORI** - OR immediate
- **ANDI** - AND immediate
- **SLLI** - Shift left logical immediate
- **SRLI** - Shift right logical immediate
- **SRAI** - Shift right arithmetic immediate
- **LW** - Load word
- **LH** - Load halfword
- **LB** - Load byte
- **LHU** - Load halfword unsigned
- **LBU** - Load byte unsigned
- **JALR** - Jump and link register

#### S-Type (Store Operations)
- **SW** - Store word
- **SH** - Store halfword
- **SB** - Store byte

#### B-Type (Branch Operations)
- **BEQ** - Branch if equal
- **BNE** - Branch if not equal
- **BLT** - Branch if less than
- **BGE** - Branch if greater than or equal
- **BLTU** - Branch if less than unsigned
- **BGEU** - Branch if greater than or equal unsigned

#### U-Type (Upper Immediate)
- **LUI** - Load upper immediate
- **AUIPC** - Add upper immediate to PC

#### J-Type (Jump Operations)
- **JAL** - Jump and link

## Architecture

### Processor Structure

```
┌─────────────────────────────────────┐
│       RV32IProcessor                │
├─────────────────────────────────────┤
│ • 32 x 32-bit Registers (x0-x31)   │
│ • Program Counter (PC)              │
│ • Configurable Memory (0-4096B)     │
│ • Cycle Counter                     │
└─────────────────────────────────────┘
```

### Execution Pipeline (Single-Cycle)

1. **Fetch** - Load instruction from memory at PC
2. **Decode** - Parse opcode, register fields, and immediates
3. **Execute** - Perform ALU operation or memory access
4. **Memory** - Access memory for load/store operations
5. **Writeback** - Update destination register (if applicable)

All stages complete in one clock cycle.

## Usage

### Basic Example

```python
from riscv_simulator import RV32IProcessor

# Create processor with 4KB memory
processor = RV32IProcessor(memory_size=4096)

# Load instructions into memory
instructions = [
    0x00500293,  # ADDI x5, x0, 5  (x5 = 5)
    0x00328293,  # ADDI x5, x5, 3  (x5 = 8)
]

processor.load_program(instructions, start_addr=0)

# Execute instructions
while processor.pc < len(instructions) * 4:
    processor.execute_cycle()

# Inspect results
processor.print_registers()
print(f"x5 = {processor.get_register(5)}")  # Output: x5 = 8
```

### Advanced Example: Loop

```python
# Program: Sum 1 to 5
# x1 = counter (starts at 1)
# x2 = accumulator (starts at 0)
instructions = [
    0x00100093,  # ADDI x1, x0, 1
    0x00000113,  # ADDI x2, x0, 0
    # Loop: x2 = x2 + x1
    0x00208133,  # ADD x2, x1, x2
    0x00108093,  # ADDI x1, x1, 1
    0x00600863,  # BLT x1, x6, -4 (branch if x1 < 6)
]
```

### API Reference

#### RV32IProcessor Class

**Constructor:**
```python
processor = RV32IProcessor(memory_size=4096)
```
- `memory_size`: Size of memory in bytes (default: 4KB)

**Methods:**
```python
processor.load_program(instructions, start_addr=0)
# Load list of 32-bit instructions starting at address

processor.execute_cycle() -> bool
# Execute one cycle, returns False on error

processor.get_register(reg: int) -> int
# Get register value (reg: 0-31)

processor.set_register(reg: int, value: int)
# Set register value

processor.print_registers()
# Print all register values in human-readable format

processor.print_memory(start=0, size=64)
# Print memory contents in hex format
```

**Properties:**
```python
processor.pc              # Program counter
processor.registers       # Dictionary of register values
processor.memory          # Memory buffer
processor.cycle_count     # Total cycles executed
processor.register_names  # Friendly register names (x0-x31)
```

## Instruction Encoding

RV32I uses 5 instruction formats:

### R-Type (Register)
```
31      25 24    20 19    15 14  12 11    7 6      0
[funct7] [rs2] [rs1] [funct3] [rd] [opcode]
```

### I-Type (Immediate)
```
31                   20 19    15 14  12 11    7 6      0
[immediate] [rs1] [funct3] [rd] [opcode]
```

### S-Type (Store)
```
31      25 24    20 19    15 14  12 11    7 6      0
[imm11:5] [rs2] [rs1] [funct3] [imm4:0] [opcode]
```

### B-Type (Branch)
```
31 30  25 24    20 19    15 14  12 11  8 7      0
[12] [10:5] [rs2] [rs1] [funct3] [4:1] [11] [opcode]
```

### U-Type (Upper Immediate)
```
31                       12 11    7 6      0
[immediate] [rd] [opcode]
```

### J-Type (Jump)
```
31 30     21 20 19    12 11    7 6      0
[20] [10:1] [11] [19:12] [rd] [opcode]
```

## Register Conventions

| Register | Name | Purpose | Saved by |
|----------|------|---------|----------|
| x0 | zero | Always zero | N/A |
| x1 | ra | Return address | Caller |
| x2 | sp | Stack pointer | Callee |
| x3 | gp | Global pointer | Caller |
| x4 | tp | Thread pointer | Caller |
| x5-x7 | t0-t2 | Temporary | Caller |
| x8 | fp/s0 | Frame pointer | Callee |
| x9 | s1 | Saved register | Callee |
| x10-x11 | a0-a1 | Function arguments | Caller |
| x12-x17 | a2-a7 | Function arguments | Caller |
| x18-x27 | s2-s11 | Saved registers | Callee |
| x28-x31 | t3-t6 | Temporary | Caller |

## Performance Characteristics

- **Throughput**: 1 instruction per cycle
- **Latency**: 1 cycle per instruction
- **Memory Access**: 1 cycle (no cache delays)

## Limitations

- **No pipelining**: Each stage takes 1 cycle
- **No caching**: Direct memory access
- **No floating-point**: RV32I only (integer base set)
- **No exceptions**: Error handling is basic
- **No 64-bit**: 32-bit architecture only

## Example Programs

### 1. Simple Addition
```python
# x5 = 10 + 20
instructions = [
    0x01400293,  # ADDI x5, x0, 20
    0x00A28293,  # ADDI x5, x5, 10
]
```

### 2. Factorial (5!)
```python
# Calculate factorial of 5
# Result stored in x10
instructions = [
    0x00500093,  # ADDI x1, x0, 5       (x1 = n)
    0x00100513,  # ADDI x10, x0, 1      (x10 = result = 1)
    # Loop: x10 = x10 * x1; x1 = x1 - 1
    0x01a50633,  # MUL x12, x10, x26    (Need M extension)
    # ... continue ...
]
```

## Testing

Run the included test program:
```bash
python riscv_simulator.py
```

Output:
```
=== RV32I Processor Simulator ===

Executing program...

Program executed.

Registers:
x 0 (zero): 0x00000000 (0)
x 5 (  t0): 0x00000008 (8)
...

Cycles executed: 2
Program Counter: 0x00000008
```

## Project Structure

```
.
├── riscv_simulator.py    # Main simulator implementation
├── README.md             # This file
└── LICENSE              # MIT License
```

## Contributing

Contributions are welcome! Areas for enhancement:
- Add support for RV32M (multiplication/division)
- Add support for RV32F (floating-point)
- Implement pipeline visualization
- Add instruction cache
- Create graphical debugger

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## References

- [RISC-V Specification](https://github.com/riscv/riscv-isa-manual)
- [RV32I Base Integer Instruction Set](https://github.com/riscv/riscv-isa-manual/blob/master/src/rv32.adoc)
- [Computer Organization: Design Essentials](https://www.elsevier.com/books/computer-organization-design-essentials/patterson/978-0-12-420119-4)

## Author

**Subash Seenu Vasan**

## Acknowledgments

- RISC-V Foundation for the ISA specification
- Python community for excellent tools and libraries
