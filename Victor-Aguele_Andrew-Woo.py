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


DEBUG = True  # Set to False to disable debug prints

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

    # Select the first operand from the register file (rf) using the register index provided in the decoded instruction.
    operand1 = rf[decoded["rs1"]]

    # Check if the control signal 'ALUSrc' is active 
    # If it is active, the second operand will be the immediate value from the decoded instruction.
    if signals.get("ALUSrc", 0) == 1:
        operand2 = decoded["imm"]
    else:
        # If 'ALUSrc' is not active, use the second register value from the register file.
        operand2 = rf[decoded["rs2"]] if "rs2" in decoded else 0

    if DEBUG:
        print(f"[Execute] Operand1 (rf[{decoded['rs1']}]) = {operand1}")
        print(f"[Execute] Operand2 = {operand2}")

    # Call the ALU function with the specified operation then store results
    alu_result = ALU(signals["ALUControl"], operand1, operand2)

    if DEBUG:
        print(f"[Execute] ALU Operation: {signals['ALUControl']} -> Result = {alu_result}")

    # check if the Branch control signal is active AND if the result of ALU is 0
    if signals.get("Branch", 0) == 1 and alu_zero == 1:
        # Calculate the branch target: starting from the current instruction's PC, add 4 (next sequential instruction),
        # then add the shifted left immediate 
        branch_target = (current_instr_pc + 4) + (decoded["imm"] << 1)
        # Update the global program counter (pc) to the branch target address to simulate a jump.
        pc = branch_target
        
        if DEBUG:
            print(f"[Execute] Branch taken. New PC = {pc}")

    # Return the result from the ALU operation 
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
    global total_clock_cycles, rf, pc

    # Increment the cycle counter to record total cycles for instruction
    total_clock_cycles += 1

    # Retrieve the mnemonic of the instruction from the decoded dictionary 
    mnemonic = decoded["mnemonic"]

    # If the MemToReg signal is active, use the memory data (for load instructions),
    # otherwise, use the ALU result (for arithmetic or logical instructions).
    value = mem_data if signals.get("MemToReg", 0) == 1 else alu_result

    # If the instruction requires writing back to a register (RegWrite is active),
    # and there is a destination register specified ("rd" exists in decoded)
    # and the destination register is not 0 (register 0 is usually constant zero),
    # then perform the register update.
    if signals.get("RegWrite", 0) == 1 and "rd" in decoded and decoded["rd"] != 0:
        # Update the register file: set the destination register to the computed value.
        rf[decoded["rd"]] = value
       
        if DEBUG:
            print(f"[WriteBack] Cycle {total_clock_cycles}: Register x{decoded['rd']} updated to {value}")

    # if a memory write is performed (indicated by MemWrite signal),
    elif signals.get("MemWrite", 0) == 1:
        if DEBUG:
            print(f"[WriteBack] Cycle {total_clock_cycles}: Memory write completed")

    # If neither a register update nor a memory write occurred,
    else:
        if DEBUG:
            print(f"[WriteBack] Cycle {total_clock_cycles}: No register update (mnemonic: {mnemonic})")

    if DEBUG:
        print(f"[WriteBack] Updated PC = {pc}\n")





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
    else:
        print("ControlUnit: Unsupported instruction", mnemonic)
    return signals




def main():
    global rf, d_mem, pc, total_clock_cycles, branch_target
    filename = input("Enter the program file name to run:\n")
    try:
        with open(filename, "r") as f:
            program = f.readlines()
    except Exception as e:
        print("Error reading file:", e)
        return

    # Remove blank lines from the program.
    program = [line.strip() for line in program if line.strip() != ""]

    rf = [0] * 32
    rf[1] = 0x20
    rf[2] = 0x5
    rf[10] = 0x70
    rf[11] = 0x4

    d_mem = [0] * 32
    # Initialize memory:
    # Address 0x70 corresponds to index 0x70//4 = 28.
    # Address 0x74 corresponds to index 29.
    d_mem[28] = 0x5
    d_mem[29] = 0x10

    # Reset PC and cycle counter
    pc = 0
    total_clock_cycles = 0

    # Run simulation until all instructions are processed.
    while True:
        instr = Fetch(program)
        # Optionally, print the fetched instruction.
        #print("Fetched Instruction:", instr)
        
        # End simulation when PC points beyond the program.
        if (pc // 4) > len(program):
            break
        decoded = Decode(instr)
        signals = ControlUnit(decoded)
        alu_result = Execute(decoded, signals)
        mem_data = Mem(alu_result, decoded, signals)
        Writeback(decoded, signals, alu_result, mem_data)
        # If PC now points beyond the program, break.
        if (pc // 4) >= len(program):
            break

    print("program terminated")
    print(f"total execution time is {total_clock_cycles} cycles")

if __name__ == "__main__":
    main()


        