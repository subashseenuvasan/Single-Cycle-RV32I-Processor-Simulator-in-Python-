# ============================================================
#   Single-Cycle RISC-V (RV32I) Processor Simulator
#   Author  : Subash (ECE, Sathyabama University)
#   Language: Python 3
# ============================================================

# ── Helpers ──────────────────────────────────────────────────

def to_signed32(val):
    """Convert unsigned 32-bit value to signed Python int."""
    val &= 0xFFFFFFFF
    if val >= 0x80000000:
        val -= 0x100000000
    return val

def to_unsigned32(val):
    return val & 0xFFFFFFFF

# ── Register File ─────────────────────────────────────────────

class RegisterFile:
    ABI = [
        "zero","ra","sp","gp","tp",
        "t0","t1","t2",
        "s0","s1",
        "a0","a1","a2","a3","a4","a5","a6","a7",
        "s2","s3","s4","s5","s6","s7","s8","s9","s10","s11",
        "t3","t4","t5","t6"
    ]

    def __init__(self):
        self.regs = [0] * 32          # x0 is always 0

    def read(self, idx):
        return self.regs[idx] if idx != 0 else 0

    def write(self, idx, val):
        if idx != 0:                  # x0 is hard-wired to 0
            self.regs[idx] = to_unsigned32(val)

    def dump(self):
        print("\n  ┌─────────────────────────────────────────┐")
        print("  │           Register File Dump            │")
        print("  ├──────────┬──────────┬──────────┬────────┤")
        for i in range(0, 32, 4):
            row = ""
            for j in range(4):
                idx = i + j
                name = self.ABI[idx].ljust(4)
                val  = self.regs[idx]
                row += f"  x{idx:02d}({name}): {val:08X}  "
            print(row)
        print("  └─────────────────────────────────────────┘")

# ── Memory ────────────────────────────────────────────────────

class Memory:
    def __init__(self, size=4096):
        self.mem = bytearray(size)

    def load_program(self, instructions, base=0):
        """Load list of 32-bit instruction words starting at base address."""
        for i, instr in enumerate(instructions):
            addr = base + i * 4
            self.mem[addr:addr+4] = instr.to_bytes(4, 'little')

    def fetch(self, addr):
        return int.from_bytes(self.mem[addr:addr+4], 'little')

    def read_word(self, addr):
        return int.from_bytes(self.mem[addr:addr+4], 'little')

    def read_half(self, addr):
        return int.from_bytes(self.mem[addr:addr+2], 'little')

    def read_byte(self, addr):
        return self.mem[addr]

    def write_word(self, addr, val):
        self.mem[addr:addr+4] = (val & 0xFFFFFFFF).to_bytes(4, 'little')

    def write_half(self, addr, val):
        self.mem[addr:addr+2] = (val & 0xFFFF).to_bytes(2, 'little')

    def write_byte(self, addr, val):
        self.mem[addr] = val & 0xFF

# ── Instruction Decoder ───────────────────────────────────────

def decode(instr):
    opcode = instr & 0x7F
    rd     = (instr >> 7)  & 0x1F
    funct3 = (instr >> 12) & 0x07
    rs1    = (instr >> 15) & 0x1F
    rs2    = (instr >> 20) & 0x1F
    funct7 = (instr >> 25) & 0x7F

    # Immediate extraction
    imm_i = to_signed32((instr >> 20) << 20) >> 20       # sign-extend 12-bit
    imm_s = to_signed32((((instr >> 25) << 5) | ((instr >> 7) & 0x1F)) << 20) >> 20
    imm_b = to_signed32(
        (((instr >> 31) & 1) << 12 |
         ((instr >> 7)  & 1) << 11 |
         ((instr >> 25) & 0x3F) << 5 |
         ((instr >> 8)  & 0xF) << 1) << 19) >> 19
    imm_u = to_signed32(instr & 0xFFFFF000)
    imm_j = to_signed32(
        (((instr >> 31) & 1) << 20 |
         ((instr >> 12) & 0xFF) << 12 |
         ((instr >> 20) & 1) << 11 |
         ((instr >> 21) & 0x3FF) << 1) << 11) >> 11

    return {
        "opcode": opcode, "rd": rd, "rs1": rs1, "rs2": rs2,
        "funct3": funct3, "funct7": funct7,
        "imm_i": imm_i, "imm_s": imm_s, "imm_b": imm_b,
        "imm_u": imm_u, "imm_j": imm_j
    }

# ── ALU ───────────────────────────────────────────────────────

def alu(op, a, b):
    a = to_signed32(a)
    b_s = to_signed32(b)
    if   op == "ADD":  return a + b
    elif op == "SUB":  return a - b
    elif op == "AND":  return a & b
    elif op == "OR":   return a | b
    elif op == "XOR":  return a ^ b
    elif op == "SLL":  return a << (b & 0x1F)
    elif op == "SRL":  return to_unsigned32(a) >> (b & 0x1F)
    elif op == "SRA":  return a >> (b & 0x1F)
    elif op == "SLT":  return 1 if a < b_s else 0
    elif op == "SLTU": return 1 if to_unsigned32(a) < to_unsigned32(b) else 0
    return 0

# ── Processor Core ────────────────────────────────────────────

class RV32I:
    def __init__(self, mem_size=4096):
        self.rf  = RegisterFile()
        self.mem = Memory(mem_size)
        self.pc  = 0
        self.cycles = 0

    def load(self, instructions, entry=0):
        self.mem.load_program(instructions, base=entry)
        self.pc = entry

    def step(self, verbose=True):
        """Fetch → Decode → Execute → Memory → Write-back (one cycle)."""
        instr_word = self.mem.fetch(self.pc)
        if instr_word == 0:          # NOP / end sentinel
            return False

        d = decode(instr_word)
        op = d["opcode"]
        pc_next = self.pc + 4

        if verbose:
            print(f"\n  PC=0x{self.pc:04X}  instr=0x{instr_word:08X}", end="")

        # ── R-type ───────────────────────────────────────────
        if op == 0x33:
            a   = self.rf.read(d["rs1"])
            b   = self.rf.read(d["rs2"])
            f3  = d["funct3"]
            f7  = d["funct7"]
            op_map = {
                (0x0, 0x00): "ADD", (0x0, 0x20): "SUB",
                (0x1, 0x00): "SLL", (0x2, 0x00): "SLT",
                (0x3, 0x00): "SLTU",(0x4, 0x00): "XOR",
                (0x5, 0x00): "SRL", (0x5, 0x20): "SRA",
                (0x6, 0x00): "OR",  (0x7, 0x00): "AND",
            }
            aop = op_map.get((f3, f7), "ADD")
            res = alu(aop, a, b)
            self.rf.write(d["rd"], res)
            if verbose: print(f"  {aop} x{d['rd']}, x{d['rs1']}, x{d['rs2']}  → {to_unsigned32(res):08X}")

        # ── I-type ALU ────────────────────────────────────────
        elif op == 0x13:
            a  = self.rf.read(d["rs1"])
            im = d["imm_i"]
            f3 = d["funct3"]
            if   f3 == 0x0: aop, res = "ADDI",  alu("ADD", a, im)
            elif f3 == 0x2: aop, res = "SLTI",  alu("SLT", a, im)
            elif f3 == 0x3: aop, res = "SLTIU", alu("SLTU",a, im)
            elif f3 == 0x4: aop, res = "XORI",  alu("XOR", a, im)
            elif f3 == 0x6: aop, res = "ORI",   alu("OR",  a, im)
            elif f3 == 0x7: aop, res = "ANDI",  alu("AND", a, im)
            elif f3 == 0x1: aop, res = "SLLI",  alu("SLL", a, im & 0x1F)
            elif f3 == 0x5:
                aop = "SRAI" if (d["funct7"] == 0x20) else "SRLI"
                res = alu("SRA" if aop == "SRAI" else "SRL", a, im & 0x1F)
            else:           aop, res = "ADDI",  alu("ADD", a, im)
            self.rf.write(d["rd"], res)
            if verbose: print(f"  {aop} x{d['rd']}, x{d['rs1']}, {im}  → {to_unsigned32(res):08X}")

        # ── LOAD ──────────────────────────────────────────────
        elif op == 0x03:
            addr = to_unsigned32(self.rf.read(d["rs1"]) + d["imm_i"])
            f3   = d["funct3"]
            if   f3 == 0x0: val = to_signed32(self.mem.read_byte(addr) | (0xFFFFFF00 if self.mem.read_byte(addr) & 0x80 else 0))
            elif f3 == 0x1: val = to_signed32(self.mem.read_half(addr) | (0xFFFF0000 if self.mem.read_half(addr) & 0x8000 else 0))
            elif f3 == 0x2: val = self.mem.read_word(addr)
            elif f3 == 0x4: val = self.mem.read_byte(addr)
            elif f3 == 0x5: val = self.mem.read_half(addr)
            else:            val = 0
            self.rf.write(d["rd"], val)
            if verbose: print(f"  LOAD x{d['rd']} ← mem[{addr:#x}] = {val:#010x}")

        # ── STORE ─────────────────────────────────────────────
        elif op == 0x23:
            addr = to_unsigned32(self.rf.read(d["rs1"]) + d["imm_s"])
            val  = self.rf.read(d["rs2"])
            f3   = d["funct3"]
            if   f3 == 0x0: self.mem.write_byte(addr, val)
            elif f3 == 0x1: self.mem.write_half(addr, val)
            elif f3 == 0x2: self.mem.write_word(addr, val)
            if verbose: print(f"  STORE mem[{addr:#x}] ← x{d['rs2']} = {val:#010x}")

        # ── BRANCH ────────────────────────────────────────────
        elif op == 0x63:
            a, b = self.rf.read(d["rs1"]), self.rf.read(d["rs2"])
            f3   = d["funct3"]
            taken = False
            if   f3 == 0x0: taken = (a == b)
            elif f3 == 0x1: taken = (a != b)
            elif f3 == 0x4: taken = (to_signed32(a)   <  to_signed32(b))
            elif f3 == 0x5: taken = (to_signed32(a)   >= to_signed32(b))
            elif f3 == 0x6: taken = (to_unsigned32(a) <  to_unsigned32(b))
            elif f3 == 0x7: taken = (to_unsigned32(a) >= to_unsigned32(b))
            name = {0:"BEQ",1:"BNE",4:"BLT",5:"BGE",6:"BLTU",7:"BGEU"}.get(f3,"BR")
            if taken:
                pc_next = self.pc + d["imm_b"]
            if verbose: print(f"  {name} → {'TAKEN' if taken else 'NOT TAKEN'}  target=0x{self.pc+d['imm_b']:04X}")

        # ── JAL ───────────────────────────────────────────────
        elif op == 0x6F:
            self.rf.write(d["rd"], self.pc + 4)
            pc_next = self.pc + d["imm_j"]
            if verbose: print(f"  JAL x{d['rd']}, 0x{pc_next:04X}")

        # ── JALR ──────────────────────────────────────────────
        elif op == 0x67:
            target  = (self.rf.read(d["rs1"]) + d["imm_i"]) & ~1
            self.rf.write(d["rd"], self.pc + 4)
            pc_next = target
            if verbose: print(f"  JALR x{d['rd']}, x{d['rs1']}, {d['imm_i']}  → 0x{pc_next:04X}")

        # ── LUI ───────────────────────────────────────────────
        elif op == 0x37:
            self.rf.write(d["rd"], d["imm_u"])
            if verbose: print(f"  LUI x{d['rd']}, 0x{(d['imm_u']>>12) & 0xFFFFF:05X}  → {to_unsigned32(d['imm_u']):08X}")

        # ── AUIPC ─────────────────────────────────────────────
        elif op == 0x17:
            res = self.pc + d["imm_u"]
            self.rf.write(d["rd"], res)
            if verbose: print(f"  AUIPC x{d['rd']}, 0x{(d['imm_u']>>12) & 0xFFFFF:05X}  → {to_unsigned32(res):08X}")

        # ── ECALL / EBREAK ────────────────────────────────────
        elif op == 0x73:
            if verbose: print("  ECALL/EBREAK — halting simulation")
            return False

        else:
            if verbose: print(f"  UNKNOWN opcode 0x{op:02X} — skipping")

        self.pc = to_unsigned32(pc_next)
        self.cycles += 1
        return True

    def run(self, max_cycles=1000, verbose=True):
        print("=" * 60)
        print("  Single-Cycle RV32I Simulator  —  Starting Execution")
        print("=" * 60)
        while self.cycles < max_cycles:
            if not self.step(verbose=verbose):
                break
        print(f"\n  ── Execution complete: {self.cycles} cycle(s) ──")
        self.rf.dump()


# ── Sample Programs ───────────────────────────────────────────

def encode_R(funct7, rs2, rs1, funct3, rd, opcode):
    return (funct7<<25)|(rs2<<20)|(rs1<<15)|(funct3<<12)|(rd<<7)|opcode

def encode_I(imm, rs1, funct3, rd, opcode):
    imm &= 0xFFF
    return (imm<<20)|(rs1<<15)|(funct3<<12)|(rd<<7)|opcode

def encode_B(imm, rs2, rs1, funct3, opcode=0x63):
    b12  = (imm >> 12) & 1
    b11  = (imm >> 11) & 1
    b10_5= (imm >>  5) & 0x3F
    b4_1 = (imm >>  1) & 0xF
    return (b12<<31)|(b10_5<<25)|(rs2<<20)|(rs1<<15)|(funct3<<12)|(b4_1<<8)|(b11<<7)|opcode

def prog_addition():
    """Compute 10 + 20 → result in x3."""
    return [
        encode_I(10, 0, 0x0, 1, 0x13),   # ADDI x1, x0, 10
        encode_I(20, 0, 0x0, 2, 0x13),   # ADDI x2, x0, 20
        encode_R(0x00, 2, 1, 0x0, 3, 0x33),  # ADD  x3, x1, x2
        0x00000073,                           # ECALL (halt)
    ]

def prog_countdown():
    """Count down from 5 to 0 using BNE loop."""
    return [
        encode_I(5, 0, 0x0, 1, 0x13),    # ADDI x1, x0, 5   (counter)
        encode_I(1, 0, 0x0, 2, 0x13),    # ADDI x2, x0, 1   (step)
        # loop: x1 = x1 - 1; if x1 != 0 goto loop
        encode_R(0x20, 2, 1, 0x0, 1, 0x33),  # SUB x1, x1, x2     (PC=8)
        encode_B(-4,   1, 0, 0x1, 0x63),     # BNE x1, x0, -4     (PC=12)
        0x00000073,                           # ECALL
    ]

def prog_fibonacci():
    """Fibonacci: F(0)=0, F(1)=1, ... F(7)=13 stored in x10."""
    instrs = [
        encode_I(0, 0, 0x0,  9, 0x13),   # ADDI x9,  x0, 0   (a = F0)
        encode_I(1, 0, 0x0, 10, 0x13),   # ADDI x10, x0, 1   (b = F1)
        encode_I(6, 0, 0x0, 11, 0x13),   # ADDI x11, x0, 6   (loop count)
        encode_I(1, 0, 0x0, 12, 0x13),   # ADDI x12, x0, 1   (decrement)
        # loop start (PC = 16):
        encode_R(0x00, 10,  9, 0x0, 13, 0x33),  # ADD  x13, x9, x10  (temp = a+b)
        encode_R(0x00, 10,  0, 0x0,  9, 0x33),  # ADD  x9,  x0, x10  (a = b)
        encode_R(0x00, 13,  0, 0x0, 10, 0x33),  # ADD  x10, x0, x13  (b = temp)
        encode_R(0x20, 12, 11, 0x0, 11, 0x33),  # SUB  x11, x11, x12
        encode_B(-16,  11,  0, 0x1, 0x63),      # BNE  x11, x0, -16
        0x00000073,
    ]
    return instrs

# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n╔══════════════════════════════════════════╗")
    print("║   RV32I Single-Cycle Processor Simulator ║")
    print("╚══════════════════════════════════════════╝\n")

    programs = {
        "1": ("Addition  (10 + 20 → x3)",         prog_addition),
        "2": ("Countdown (5 → 0 via BNE loop)",    prog_countdown),
        "3": ("Fibonacci (F7 = 13 in x10)",        prog_fibonacci),
    }

    print("  Select a program to simulate:")
    for k, (name, _) in programs.items():
        print(f"    [{k}] {name}")

    choice = input("\n  Enter choice (1/2/3): ").strip()
    if choice not in programs:
        print("  Invalid choice — running Addition by default.")
        choice = "1"

    name, prog_fn = programs[choice]
    print(f"\n  Running: {name}\n")

    cpu = RV32I()
    cpu.load(prog_fn())
    cpu.run(max_cycles=200, verbose=True)