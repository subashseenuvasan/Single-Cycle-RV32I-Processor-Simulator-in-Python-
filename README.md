🖥️ Single-Cycle RV32I Processor Simulator
A fully functional RISC-V (RV32I) processor simulator built in Python, implementing the complete single-cycle datapath with fetch → decode → execute → memory → write-back stages.
Built as part of an ECE project portfolio — Sathyabama University
📌 What is RISC-V?
RISC-V is an open-source, royalty-free Instruction Set Architecture (ISA) based on Reduced Instruction Set Computer (RISC) principles. Unlike ARM or x86, anyone can use it freely without licensing fees — making it ideal for academic and research projects.
✨ Features
✅ Full RV32I base integer instruction set support
✅ 32 general-purpose registers (x0–x31) with ABI names
✅ All instruction formats: R, I, S, B, U, J
✅ 10 ALU operations: ADD, SUB, AND, OR, XOR, SLL, SRL, SRA, SLT, SLTU
✅ Branch instructions: BEQ, BNE, BLT, BGE, BLTU, BGEU
✅ Memory instructions: LB, LH, LW, LBU, LHU, SB, SH, SW
✅ Jump instructions: JAL, JALR
✅ Upper immediate: LUI, AUIPC
✅ Cycle-accurate verbose execution trace
✅ Register file dump after execution
✅ 3 built-in sample programs
🏗️ Architecture
┌─────────────┐    ┌──────────┐    ┌─────┐    ┌────────┐    ┌────────────┐
│  Instruction │ →  │  Decode  │ →  │ ALU │ →  │ Memory │ →  │ Write-Back │
│    Memory    │    │ (Control)│    │     │    │ Access │    │  (Reg File)│
└─────────────┘    └──────────┘    └─────┘    └────────┘    └────────────┘
       ↑
  PC (Program Counter)

Core Components
RegisterFile:
32 × 32-bit registers; x0 hardwired to 0
Memory:
Byte-addressable 4KB memory (load/store support)
decode():
Extracts opcode, rd, rs1, rs2, funct3, funct7, all immediates
alu():
Performs 10 arithmetic/logic operations
RV32I:
Main processor — single-cycle fetch-decode-execute loop

🚀 Getting Started
Requirements
Python 3.6+
No external libraries needed
Installation
git clone https://github.com/your-username/riscv-simulator.git
cd riscv-simulator
