"""
Single-Cycle RV32I Processor Simulator in Python
A RISC-V 32-bit processor simulator implementing the base integer instruction set.
"""

import struct
from typing import Dict, List, Tuple, Optional
from enum import IntEnum


class OpCode(IntEnum):
    """RV32I Instruction Opcodes"""
    LOAD = 0x03
    IMMEDIATE = 0x13
    AUIPC = 0x17
    STORE = 0x23
    REGISTER = 0x33
    LUI = 0x37
    BRANCH = 0x63
    JALR = 0x67
    JAL = 0x6F
    SYSTEM = 0x73


class Funct3(IntEnum):
    """Funct3 field encoding for various instruction types"""
    # Load/Store
    LB = 0x0
    LH = 0x1
    LW = 0x2
    LBU = 0x4
    LHU = 0x5
    
    SB = 0x0
    SH = 0x1
    SW = 0x2
    
    # Arithmetic/Logic
    ADD_SUB = 0x0
    SLL = 0x1
    SLT = 0x2
    SLTU = 0x3
    XOR = 0x4
    SRL_SRA = 0x5
    OR = 0x6
    AND = 0x7
    
    # Branch
    BEQ = 0x0
    BNE = 0x1
    BLT = 0x4
    BGE = 0x5
    BLTU = 0x6
    BGEU = 0x7


class RV32IProcessor:
    """Single-cycle RV32I RISC-V Processor Simulator"""
    
    def __init__(self, memory_size: int = 4096):
        """Initialize the processor with registers and memory"""
        self.registers: Dict[int, int] = {i: 0 for i in range(32)}
        self.pc: int = 0  # Program Counter
        self.memory: bytearray = bytearray(memory_size)
        self.memory_size = memory_size
        self.cycle_count: int = 0
        
        # Register names for easier debugging
        self.register_names = [
            'zero', 'ra', 'sp', 'gp', 'tp', 't0', 't1', 't2',
            'fp', 's1', 'a0', 'a1', 'a2', 'a3', 'a4', 'a5',
            'a6', 'a7', 's2', 's3', 's4', 's5', 's6', 's7',
            's8', 's9', 's10', 's11', 't3', 't4', 't5', 't6'
        ]
    
    def load_program(self, instructions: List[int], start_addr: int = 0) -> None:
        """Load a list of 32-bit instructions into memory"""
        for i, instr in enumerate(instructions):
            addr = start_addr + i * 4
            self._write_memory(addr, instr, 4)
        self.pc = start_addr
    
    def _read_memory(self, addr: int, size: int) -> int:
        """Read from memory (1, 2, or 4 bytes)"""
        if addr + size > self.memory_size or addr < 0:
            raise MemoryError(f"Memory access out of bounds: {addr}")
        
        value = 0
        for i in range(size):
            value |= self.memory[addr + i] << (8 * i)
        return value
    
    def _write_memory(self, addr: int, value: int, size: int) -> None:
        """Write to memory (1, 2, or 4 bytes)"""
        if addr + size > self.memory_size or addr < 0:
            raise MemoryError(f"Memory access out of bounds: {addr}")
        
        for i in range(size):
            self.memory[addr + i] = (value >> (8 * i)) & 0xFF
    
    def _sign_extend(self, value: int, bits: int) -> int:
        """Sign extend a value from bits to 32 bits"""
        if value & (1 << (bits - 1)):
            return value | (-1 << bits)
        return value
    
    def _decode_instruction(self, instr: int) -> Tuple[int, int, int, int, int, int]:
        """Decode a 32-bit instruction into fields"""
        opcode = instr & 0x7F
        rd = (instr >> 7) & 0x1F
        funct3 = (instr >> 12) & 0x7
        rs1 = (instr >> 15) & 0x1F
        rs2 = (instr >> 20) & 0x1F
        funct7 = (instr >> 25) & 0x7F
        
        return opcode, rd, rs1, rs2, funct3, funct7
    
    def _extract_immediate(self, instr: int, instr_type: str) -> int:
        """Extract and sign-extend immediate value based on instruction type"""
        if instr_type == 'I':  # I-type
            imm = instr >> 20
            return self._sign_extend(imm, 12)
        elif instr_type == 'S':  # S-type
            imm11_5 = (instr >> 25) & 0x7F
            imm4_0 = (instr >> 7) & 0x1F
            imm = (imm11_5 << 5) | imm4_0
            return self._sign_extend(imm, 12)
        elif instr_type == 'B':  # B-type
            imm12 = (instr >> 31) & 1
            imm11 = (instr >> 7) & 1
            imm10_5 = (instr >> 25) & 0x3F
            imm4_1 = (instr >> 8) & 0x0F
            imm = (imm12 << 12) | (imm11 << 11) | (imm10_5 << 5) | (imm4_1 << 1)
            return self._sign_extend(imm, 13)
        elif instr_type == 'U':  # U-type
            imm = instr & 0xFFFFF000
            return imm
        elif instr_type == 'J':  # J-type
            imm20 = (instr >> 31) & 1
            imm19_12 = (instr >> 12) & 0xFF
            imm11 = (instr >> 20) & 1
            imm10_1 = (instr >> 21) & 0x3FF
            imm = (imm20 << 20) | (imm19_12 << 12) | (imm11 << 11) | (imm10_1 << 1)
            return self._sign_extend(imm, 21)
        return 0
    
    def _set_register(self, rd: int, value: int) -> None:
        """Set a register value (x0 is always 0)"""
        if rd != 0:
            self.registers[rd] = value & 0xFFFFFFFF
    
    def execute_cycle(self) -> bool:
        """Execute one cycle of the processor"""
        # Fetch
        instr = self._read_memory(self.pc, 4)
        
        # Decode
        opcode, rd, rs1, rs2, funct3, funct7 = self._decode_instruction(instr)
        
        # Execute and Memory/Writeback
        try:
            if opcode == OpCode.IMMEDIATE:
                self._execute_immediate(instr, rd, rs1, funct3)
            elif opcode == OpCode.REGISTER:
                self._execute_register(rd, rs1, rs2, funct3, funct7)
            elif opcode == OpCode.LOAD:
                self._execute_load(instr, rd, rs1, funct3)
            elif opcode == OpCode.STORE:
                self._execute_store(instr, rs1, rs2, funct3)
            elif opcode == OpCode.BRANCH:
                self._execute_branch(instr, rs1, rs2, funct3)
            elif opcode == OpCode.JAL:
                self._execute_jal(instr, rd)
            elif opcode == OpCode.JALR:
                self._execute_jalr(instr, rd, rs1)
            elif opcode == OpCode.LUI:
                self._execute_lui(instr, rd)
            elif opcode == OpCode.AUIPC:
                self._execute_auipc(instr, rd)
            else:
                return False
        except Exception as e:
            print(f"Execution error: {e}")
            return False
        
        self.cycle_count += 1
        return True
    
    def _execute_immediate(self, instr: int, rd: int, rs1: int, funct3: int) -> None:
        """Execute I-type immediate instructions"""
        imm = self._extract_immediate(instr, 'I')
        val1 = self.registers[rs1]
        
        if funct3 == Funct3.ADD_SUB:  # ADDI
            self._set_register(rd, val1 + imm)
            self.pc += 4
        elif funct3 == Funct3.SLT:  # SLTI
            self._set_register(rd, 1 if self._sign_extend(val1, 32) < imm else 0)
            self.pc += 4
        elif funct3 == Funct3.SLTU:  # SLTIU
            self._set_register(rd, 1 if val1 < (imm & 0xFFFFFFFF) else 0)
            self.pc += 4
        elif funct3 == Funct3.XOR:  # XORI
            self._set_register(rd, val1 ^ imm)
            self.pc += 4
        elif funct3 == Funct3.OR:  # ORI
            self._set_register(rd, val1 | imm)
            self.pc += 4
        elif funct3 == Funct3.AND:  # ANDI
            self._set_register(rd, val1 & imm)
            self.pc += 4
        elif funct3 == Funct3.SLL:  # SLLI
            shamt = imm & 0x1F
            self._set_register(rd, val1 << shamt)
            self.pc += 4
        elif funct3 == Funct3.SRL_SRA:  # SRLI or SRAI
            shamt = imm & 0x1F
            if imm & 0x400:  # SRAI
                self._set_register(rd, self._sign_extend(val1, 32) >> shamt)
            else:  # SRLI
                self._set_register(rd, val1 >> shamt)
            self.pc += 4
    
    def _execute_register(self, rd: int, rs1: int, rs2: int, funct3: int, funct7: int) -> None:
        """Execute R-type register instructions"""
        val1 = self.registers[rs1]
        val2 = self.registers[rs2]
        
        if funct3 == Funct3.ADD_SUB:
            if funct7 == 0:  # ADD
                self._set_register(rd, val1 + val2)
            else:  # SUB
                self._set_register(rd, val1 - val2)
        elif funct3 == Funct3.SLL:  # SLL
            self._set_register(rd, val1 << (val2 & 0x1F))
        elif funct3 == Funct3.SLT:  # SLT
            self._set_register(rd, 1 if self._sign_extend(val1, 32) < self._sign_extend(val2, 32) else 0)
        elif funct3 == Funct3.SLTU:  # SLTU
            self._set_register(rd, 1 if val1 < val2 else 0)
        elif funct3 == Funct3.XOR:  # XOR
            self._set_register(rd, val1 ^ val2)
        elif funct3 == Funct3.SRL_SRA:
            if funct7 == 0:  # SRL
                self._set_register(rd, val1 >> (val2 & 0x1F))
            else:  # SRA
                self._set_register(rd, self._sign_extend(val1, 32) >> (val2 & 0x1F))
        elif funct3 == Funct3.OR:  # OR
            self._set_register(rd, val1 | val2)
        elif funct3 == Funct3.AND:  # AND
            self._set_register(rd, val1 & val2)
        
        self.pc += 4
    
    def _execute_load(self, instr: int, rd: int, rs1: int, funct3: int) -> None:
        """Execute I-type load instructions"""
        imm = self._extract_immediate(instr, 'I')
        addr = self.registers[rs1] + imm
        
        if funct3 == Funct3.LW:  # LW
            value = self._read_memory(addr, 4)
            self._set_register(rd, self._sign_extend(value, 32))
        elif funct3 == Funct3.LH:  # LH
            value = self._read_memory(addr, 2)
            self._set_register(rd, self._sign_extend(value, 16))
        elif funct3 == Funct3.LB:  # LB
            value = self._read_memory(addr, 1)
            self._set_register(rd, self._sign_extend(value, 8))
        elif funct3 == Funct3.LHU:  # LHU
            value = self._read_memory(addr, 2)
            self._set_register(rd, value & 0xFFFF)
        elif funct3 == Funct3.LBU:  # LBU
            value = self._read_memory(addr, 1)
            self._set_register(rd, value & 0xFF)
        
        self.pc += 4
    
    def _execute_store(self, instr: int, rs1: int, rs2: int, funct3: int) -> None:
        """Execute S-type store instructions"""
        imm = self._extract_immediate(instr, 'S')
        addr = self.registers[rs1] + imm
        value = self.registers[rs2]
        
        if funct3 == Funct3.SW:  # SW
            self._write_memory(addr, value, 4)
        elif funct3 == Funct3.SH:  # SH
            self._write_memory(addr, value & 0xFFFF, 2)
        elif funct3 == Funct3.SB:  # SB
            self._write_memory(addr, value & 0xFF, 1)
        
        self.pc += 4
    
    def _execute_branch(self, instr: int, rs1: int, rs2: int, funct3: int) -> None:
        """Execute B-type branch instructions"""
        imm = self._extract_immediate(instr, 'B')
        val1 = self._sign_extend(self.registers[rs1], 32)
        val2 = self._sign_extend(self.registers[rs2], 32)
        
        branch_taken = False
        if funct3 == Funct3.BEQ:  # BEQ
            branch_taken = val1 == val2
        elif funct3 == Funct3.BNE:  # BNE
            branch_taken = val1 != val2
        elif funct3 == Funct3.BLT:  # BLT
            branch_taken = val1 < val2
        elif funct3 == Funct3.BGE:  # BGE
            branch_taken = val1 >= val2
        elif funct3 == Funct3.BLTU:  # BLTU
            branch_taken = self.registers[rs1] < self.registers[rs2]
        elif funct3 == Funct3.BGEU:  # BGEU
            branch_taken = self.registers[rs1] >= self.registers[rs2]
        
        if branch_taken:
            self.pc = self.pc + imm
        else:
            self.pc += 4
    
    def _execute_jal(self, instr: int, rd: int) -> None:
        """Execute J-type JAL instruction"""
        imm = self._extract_immediate(instr, 'J')
        self._set_register(rd, self.pc + 4)
        self.pc = self.pc + imm
    
    def _execute_jalr(self, instr: int, rd: int, rs1: int) -> None:
        """Execute I-type JALR instruction"""
        imm = self._extract_immediate(instr, 'I')
        self._set_register(rd, self.pc + 4)
        self.pc = (self.registers[rs1] + imm) & 0xFFFFFFFE
    
    def _execute_lui(self, instr: int, rd: int) -> None:
        """Execute U-type LUI instruction"""
        imm = self._extract_immediate(instr, 'U')
        self._set_register(rd, imm)
        self.pc += 4
    
    def _execute_auipc(self, instr: int, rd: int) -> None:
        """Execute U-type AUIPC instruction"""
        imm = self._extract_immediate(instr, 'U')
        self._set_register(rd, self.pc + imm)
        self.pc += 4
    
    def get_register(self, reg: int) -> int:
        """Get the value of a register"""
        return self.registers[reg]
    
    def set_register(self, reg: int, value: int) -> None:
        """Set the value of a register"""
        self._set_register(reg, value)
    
    def print_registers(self) -> None:
        """Print all register values"""
        print("Registers:")
        for i in range(32):
            name = self.register_names[i]
            value = self.registers[i]
            print(f"x{i:2d} ({name:>4s}): 0x{value:08X} ({value})")
    
    def print_memory(self, start: int = 0, size: int = 64) -> None:
        """Print memory contents"""
        print(f"\nMemory (0x{start:04X} - 0x{start+size:04X}):")
        for addr in range(start, min(start + size, self.memory_size), 16):
            hex_str = ' '.join(f'{self.memory[addr+i]:02X}' for i in range(16) if addr+i < self.memory_size)
            print(f"0x{addr:04X}: {hex_str}")


def main():
    """Example: Simple test program"""
    # Create processor with 4KB memory
    processor = RV32IProcessor(memory_size=4096)
    
    # Example: Load 5 into x5, add 3 to get 8 in x5
    # ADDI x5, x0, 5  (opcode: 0x13, funct3: 0x0)
    # ADDI x5, x5, 3
    instructions = [
        0x00500293,  # ADDI x5, x0, 5
        0x00328293,  # ADDI x5, x5, 3
        0x00000033,  # ADD x0, x0, x0 (NOP)
    ]
    
    processor.load_program(instructions)
    
    print("=== RV32I Processor Simulator ===")
    print()
    print("Executing program...\n")
    
    # Execute the program
    while processor.pc < len(instructions) * 4:
        if not processor.execute_cycle():
            break
    
    print("Program executed.\n")
    processor.print_registers()
    print(f"\nCycles executed: {processor.cycle_count}")
    print(f"Program Counter: 0x{processor.pc:08X}")


if __name__ == "__main__":
    main()
