"""
Supports the following instructions:
lw, sw, add, addi, sub, and, andi, or, ori, beq


Functions to implement:
  • Fetch()       : Reads one instruction from the input program file per cycle.
  • Decode()      : Decodes the fetched 32-bit instruction and performs sign extension.
  • Execute()     : Uses an ALU to perform computation and (if needed) computes the branch target.
  • Mem()         : Handles data memory accesses (for lw and sw).
  • Writeback()   : Writes back ALU or memory results to the register file and increments the cycle counter.
  • ControlUnit() : Generates control signals based on the decoded instruction.
  • ALU()         : Performs the operations specified by op on operand1 and operand2

  
Global Variables:
  pc                : Program counter (initialized to 0)
  branch_target     : Updated by Execute() when a branch is taken
  total_clock_cycles: Cycle counter (incremented each time an instruction completes)
  alu_zero          : 1-bit flag from the ALU (used for branch decisions)
  rf                : 32-entry register file
  d_mem             : 32-entry data memory (each entry is 4 bytes)
  current_instr_pc   : Holds the PC of the instruction currently being executed
"""


#Global Variables
pc = 0                   # Program Counter: holds the memory address of the current instruction to be fetched.
next_pc = 0              # Next Program Counter: stores the computed address for the next instruction (usually pc + 4).
branch_target = 0        # Branch Target: holds the target address when a branch instruction (e.g., beq) is taken.
total_clock_cycles = 0   # Total Clock Cycles: counts the number of instruction cycles (or ticks) that have been executed.
alu_zero = 0             # ALU Zero Flag: indicates whether the result from the ALU is zero 
rf = [0] * 32            # 32-entry register file
d_mem = [0] * 32         # 32-entry data memory; each entry is 4 bytes
current_instr_pc = 0     # holds the PC of the instruction being executed


DEBUG = False  # Set to False to disable debug prints
# ABI names for x0–x31
reg_names = {
    0:  "zero", 1:  "ra",  2:  "sp",  3:  "gp",  4:  "tp",
    5:  "t0",    6:  "t1",  7:  "t2",  8:  "s0",  9:  "s1",
    10: "a0",   11:  "a1", 12:  "a2", 13:  "a3", 14:  "a4", 15: "a5",
    16: "a6",   17:  "a7", 18:  "s2", 19:  "s3", 20:  "s4", 21: "s5",
    22: "s6",   23:  "s7", 24:  "s8", 25:  "s9", 26: "s10",27: "s11",
    28: "t3",   29:  "t4", 30:  "t5", 31:  "t6",
}
# After reg_names dict, add:
use_abi_names = True   # default; will override in main()

def Fetch(program):
    global pc, next_pc, branch_target, current_instr_pc

    # Store the current value of the program counter in current_instr_pc.
    current_instr_pc = pc
    
    # Compute the next instruction's address by adding 4 to the current PC.
    # Instructions are 4 bytes long, so we increment by 4.
    next_pc = pc + 4
    
    # Fetch the instruction from the program using the current program counter.
    # Since pc is in bytes, dividing by 4 converts it to the correct index in the program list.
    instruction = program[pc // 4]
    
    if DEBUG:
        print(f"[Fetch] PC = {pc} -> Fetched Instruction: {instruction}")
    
    # Update the global program counter to the next instruction's address.
    pc = next_pc
    
    if DEBUG:
        print(f"[Fetch] Updated PC = {pc}")
    
    # Return the fetched instruction 
    return instruction



def Decode(instruction):
    # Helper function to sign extend a binary string.
    def sign_extend(binary_string, num_bits):
        x = int(binary_string, 2)
        if binary_string[0] == '1':
            x -= 2 ** num_bits
        return x

    # Function to determine instruction type
    def determineInstructionType(machineCode):
        opcodes = {
            "0110011": "R", 
            "0000011": "I", "0010011": "I", "1100111": "I",
            "0100011": "S", 
            "1100011": "SB", 
            "1101111": "UJ"
        }
        return opcodes[machineCode[25:]]

    # Function to determine mnemonic
    def determineMnemonic(machineCode, type):
        if type == "R":
            funct_3_7 = {
                "0000000000": "add", 
                "0000100000": "sub", 
                "0010000000": "sll",
                "0100000000": "slt", 
                "0110000000": "sltu", 
                "1000000000": "xor",
                "1010000000": "srl", 
                "1010100000": "sra", 
                "1100000000": "or",
                "1110000000": "and"    
            }
            return funct_3_7[machineCode[17:20] + machineCode[:7]]
        elif type == "I" and machineCode[25:] == "0000011":
            funct3 = {"000": "lb", "001": "lh", "010": "lw"}
            return funct3[machineCode[17:20]]
        elif type == "I" and machineCode[25:] == "0010011":
            funct3 = {"000": "addi", "001": "slli", "010": "slti", "011": "sltiu",
                      "100": "xori", "110": "ori", "111": "andi"}
            return funct3[machineCode[17:20]]
        elif type == "I" and machineCode[25:] == "1100111":
            return "jalr"
        elif type == "S":
            funct3 = {"000": "sb", "001": "sh", "010": "sw", "011": "sd"}
            return funct3[machineCode[17:20]]
        elif type == "SB":
            funct3 = {"000": "beq", "001": "bne", "100": "blt", "101": "bge"}
            return funct3[machineCode[17:20]]
        elif type == "UJ":
            return "jal"

    machineCode = instruction.strip()
    type = determineInstructionType(machineCode)
    mnemonic = determineMnemonic(machineCode, type)
    decoded = {"type": type, "mnemonic": mnemonic}

    if type == "R":
        decoded["rs1"] = int(machineCode[12:17], 2)
        decoded["rs2"] = int(machineCode[7:12], 2)
        decoded["rd"]  = int(machineCode[20:25], 2)
        decoded["imm"] = None
    elif type == "I":
        decoded["rs1"] = int(machineCode[12:17], 2)
        decoded["rd"]  = int(machineCode[20:25], 2)
        decoded["imm"] = sign_extend(machineCode[0:12], 12)
    elif type == "S":
        decoded["rs1"] = int(machineCode[12:17], 2)
        decoded["rs2"] = int(machineCode[7:12], 2)
        imm_binary = machineCode[0:7] + machineCode[20:25]
        decoded["imm"] = sign_extend(imm_binary, 12)
    elif type == "SB":
        decoded["rs1"] = int(machineCode[12:17], 2)
        decoded["rs2"] = int(machineCode[7:12], 2)
        imm_binary = machineCode[0] + machineCode[24] + machineCode[1:7] + machineCode[20:24] + "0"
        decoded["imm"] = sign_extend(imm_binary, 13)
    elif type == "UJ":
        decoded["rd"] = int(machineCode[20:25], 2)
        imm_binary = machineCode[0] + machineCode[12:20] + machineCode[11] + machineCode[1:11] + "0"
        decoded["imm"] = sign_extend(imm_binary, 21)

    if DEBUG:
        print(f"[Decode] Decoded Instruction: {decoded}")
    return decoded



#handles acutal computation specified by the instruction
def Execute(decoded, signals):
    global rf, pc, current_instr_pc, branch_target, alu_zero

    # --- operands ---
    operand1 = rf[decoded["rs1"]] if "rs1" in decoded else 0

    if signals.get("ALUSrc", 0) == 1:
        operand2 = decoded["imm"]
    else:
        operand2 = rf[decoded["rs2"]] if "rs2" in decoded else 0

    # ----- Handle JAL -----
    if decoded["mnemonic"] == "jal":
        branch_target = current_instr_pc + decoded["imm"]
        pc = branch_target
        return None

    # ----- Handle JALR -----
    if decoded["mnemonic"] == "jalr":
        base = rf[decoded["rs1"]]
        branch_target = (base + decoded["imm"]) & ~1
        pc = branch_target
        return None

    # --- Normal ALU + branch ---
    alu_result = ALU(signals["ALUControl"], operand1, operand2)
    alu_zero   = (alu_result == 0)

    if signals.get("Branch", 0) and alu_zero:
        branch_target = (current_instr_pc + 4) + (decoded["imm"] << 1)
        pc = branch_target

    return alu_result





#handles data memory accesses(load and store)
def Mem(alu_result, decoded, signals):
    global d_mem, rf

    # Check if the instruction involves a memory read operation (lw).
    if signals.get("MemRead", 0) == 1:
        # Calculate the memory index from the effective address.
        # Since each memory entry is 4 bytes, divide by 4 
        index = alu_result // 4
        
        # Ensure that the computed index is within the bounds of the data memory array.
        if 0 <= index < len(d_mem):
            # Read the data stored at the computed index in memory.
            data = d_mem[index]
            
            if DEBUG:
                print(f"[Mem] lw: Reading data {data} from memory index {index}")
                
            # Return the read data to be used in the Writeback stage.
            return data
        else:
            print("Memory Read Error: Address out of bounds")
            return 0

    # If the instruction is a memory write (sw) 
    elif signals.get("MemWrite", 0) == 1:
        # Calculate the memory index using the ALU result, the same way as for memory reads.
        index = alu_result // 4
        
        # Check if the calculated index is within the valid range of memory addresses.
        if 0 <= index < len(d_mem):
            # Write data to the memory: take the value from the source register (rs2) in the decoded instruction.
            d_mem[index] = rf[decoded["rs2"]]
            
            if DEBUG:
                print(f"[Mem] sw: Writing data {rf[decoded['rs2']]} to memory index {index}")
        else:
            
            print("Memory Write Error: Address out of bounds")
    
    # Return None if no memory operation is performed.
    return None

#update the register file
def Writeback(decoded, signals, alu_result, mem_data):
    global total_clock_cycles, rf, pc, d_mem, use_abi_names

    total_clock_cycles += 1
    modifications = []

    # JAL / JALR link write-back
    if decoded["mnemonic"] in ("jal", "jalr"):
        rd = decoded.get("rd")
        retaddr = current_instr_pc + 4
        if rd not in (None, 0):
            rf[rd] = retaddr
            # choose name:
            name = (reg_names[rd] if use_abi_names else f"x{rd}")
            modifications.append(f"{name} is modified to {hex(retaddr)}")

    else:
        # normal register write-back
        write_val = mem_data if signals.get("MemToReg", 0) else alu_result
        rd = decoded.get("rd")
        if signals.get("RegWrite", 0) and rd not in (None, 0):
            rf[rd] = write_val
            name = (reg_names[rd] if use_abi_names else f"x{rd}")
            modifications.append(f"{name} is modified to {hex(write_val)}")

        # store (sw)
        if signals.get("MemWrite", 0):
            addr = alu_result
            idx  = addr // 4
            if 0 <= idx < len(d_mem):
                val = rf[decoded["rs2"]]
                d_mem[idx] = val
                modifications.append(f"memory {hex(addr)} is modified to {hex(val)}")

    # always report PC
    modifications.append(f"pc is modified to {hex(pc)}")

    # print
    print(f"total_clock_cycles {total_clock_cycles} :")
    for m in modifications:
        print(m)
    print()








def ALU(op, operand1, operand2):
    global alu_zero
    # Initialize the result to 0.
    result = 0

    # Check the operation type specified by 'op'.
    if op == "add":
        # If the operation is addition, add operand1 and operand2.
        result = operand1 + operand2
    elif op == "sub":
        # For subtraction, subtract operand2 from operand1.
        result = operand1 - operand2
        
        # Set the alu_zero flag to 1 if the result is zero, else set it to 0.
        # This is used to determine equality (for example, in branch instructions like beq).
        alu_zero = 1 if result == 0 else 0
        
    elif op == "and":
        # For logical AND, perform bitwise AND on operand1 and operand2.
        result = operand1 & operand2
    elif op == "or":
        # For logical OR, perform bitwise OR on operand1 and operand2.
        result = operand1 | operand2
    else:
        # If the operation is not supported, print an error message.
        print("ALU: Unsupported operation", op)
    
    # Return the computed result.
    return result



def ControlUnit(decoded):
    mnemonic = decoded["mnemonic"]
    signals = {}
    # Defaults
    signals["RegWrite"] = 0
    signals["MemRead"] = 0
    signals["MemWrite"] = 0
    signals["ALUSrc"] = 0
    signals["Branch"] = 0
    signals["MemToReg"] = 0
    # Set control signals based on instruction type
    if mnemonic == "lw":
        signals["RegWrite"] = 1
        signals["MemRead"] = 1
        signals["ALUSrc"] = 1
        signals["MemToReg"] = 1
        signals["ALUControl"] = "add"
    elif mnemonic == "sw":
        signals["MemWrite"] = 1
        signals["ALUSrc"] = 1
        signals["ALUControl"] = "add"
    elif mnemonic in ["add", "sub", "and", "or"]:
        signals["RegWrite"] = 1
        signals["ALUSrc"] = 0
        signals["ALUControl"] = mnemonic  # direct mapping
    elif mnemonic in ["addi", "andi", "ori"]:
        signals["RegWrite"] = 1
        signals["ALUSrc"] = 1
        # For addi, andi, ori, the ALU operation is the same as their mnemonic without the "i"
        if mnemonic == "addi":
            signals["ALUControl"] = "add"
        elif mnemonic == "andi":
            signals["ALUControl"] = "and"
        elif mnemonic == "ori":
            signals["ALUControl"] = "or"
    elif mnemonic == "beq":
        signals["Branch"] = 1
        signals["ALUSrc"] = 0
        signals["ALUControl"] = "sub"  # to check for equality
    elif mnemonic == "jal":
        signals["RegWrite"] = 1
        signals["MemRead"] = 0
        signals["MemWrite"] = 0
        signals["ALUSrc"] = 1
        signals["Branch"] = 1
        signals["MemToReg"] = 0
        signals["ALUControl"] = "add"
    elif mnemonic == "jalr":
        signals["RegWrite"] = 1
        signals["MemRead"] = 0
        signals["MemWrite"] = 0
        signals["ALUSrc"] = 1
        signals["Branch"] = 0
        signals["MemToReg"] = 0
        signals["ALUControl"] = "add"
    else:
        print("ControlUnit: Unsupported instruction", mnemonic)
    return signals


def main():
    global rf, d_mem, pc, total_clock_cycles, use_abi_names

    filename = input("Enter the program file name to run:\n")
    with open(filename) as f:
        program = [l.strip() for l in f if l.strip()]

    # ─── reset everything ─────────────────────────────
    rf = [0] * 32
    d_mem = [0] * 32
    pc = 0
    total_clock_cycles = 0

    # ─── per–sample initialization ────────────────────
    if filename.endswith("sample_part1.txt"):
        # sample 1 needs x1=0x20, x2=0x5, a0=0x70, a1=0x4
        use_abi_names = False
        rf[1]  = 0x20    # x1
        rf[2]  = 0x5     # x2
        rf[10] = 0x70    # a0
        rf[11] = 0x4     # a1
        # memory at 0x70/4=28 and 0x74/4=29
        d_mem[28] = 0x5
        d_mem[29] = 0x10

    else:
        # sample 2 needs s0,a0,a1,a2,a3
        use_abi_names = True
        rf[8]  = 0x20    # s0
        rf[10] = 0x5     # a0
        rf[11] = 0x2     # a1
        rf[12] = 0xa     # a2
        rf[13] = 0xf     # a3
        # leave d_mem as zeros

    # ─── run the pipeline ────────────────────────────
    while (pc // 4) < len(program):
        instr    = Fetch(program)
        decoded  = Decode(instr)
        signals  = ControlUnit(decoded)
        alu_res  = Execute(decoded, signals)
        mem_data = Mem(alu_res, decoded, signals)
        Writeback(decoded, signals, alu_res, mem_data)

    print("program terminated:")
    print(f"total execution time is {total_clock_cycles} cycles")



if __name__ == "__main__":
    main()
