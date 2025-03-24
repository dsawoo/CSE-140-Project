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
pc = 0
branch_target = 0
total_clock_cycles = 0
alu_zero = 0
rf = [0] * 32
d_mem = [0] * 32
current_instr_pc = 0




#convert binary string to int
#ensure negative # are correctly represented when using fixed number of bits
#Andrew
def sign_extend(binary_string, num_bits):
    x = int(binary_string, 2)
    if binary_string[0] == '1':
        x -= 2 ** num_bits
    return x


#Victor
def determineInstructionType(machineCode):
    opcodes = {"0110011": "R", 
               "0000011": "I", "0010011": "I", "1100111": "I",
               "0100011": "S", 
               "1100011": "SB", 
               "1101111": "UJ"
            }
    return opcodes[machineCode[25:]]

#Victor
def determineMnemonic(machineCode, type):
    if type == "R":
        funct_3_7 = {"0000000000": "add", "0000000001": "sub", "0010000000": "sll",
                     "0100000000": "slt", "0110000000": "sltu", "1000000000": "xor",
                     "1010000000": "srl", "1010100000": "sra", "1100000000": "or",
                     "1110000000": "and"    
                    }
        return funct_3_7[machineCode[17:20] + machineCode[:7]]
    
    elif type == "I" and machineCode[25:] == "0000011":
        funct3 = {"000": "lb", "001": "lh", "010": "lw"}
        return funct3[machineCode[17:20]]
    
    elif type == "I" and machineCode[25:] == "0010011":
        if machineCode[:12] == "000000000000" or machineCode[:12] == "010000000000":
            funct_3_imm = {"1010000000": "srli", "1010100000": "srai"}
            return funct_3_imm[machineCode[17:20] + machineCode[0:12]]
        else:
            funct3 = {"000": "addi", "001": "slli", "010": "slti", "011": "sltiu", "100": "xori",
                        "110": "ori", "111": "andi"
                    }
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

def parse_instruction(machineCode):
    
def Fetch(program):

def Decode(instructions):
    

def ALU(op, operand1, operand2):


def Execute(decoded, signals):


def Mem(alu_result, decoded, signals):

def Writeback(decoded, signals, alu_result, mem_data):

def ControlUnit(decoded):
    
    
    
    
    
    

def main():
    global pc, total_clock_cycles, rf, d_mem
    filename = input("Enter the program file name to run:\n")
    try:
        with open(filename, "r") as f:
            program = f.readlines()
    except Exception as e:
        print("Error reading file:", e)
        return

    # Remove blank lines from the program.
    program = [line.strip() for line in program if line.strip() != ""]

    #initializatize all registers and memory start at 0.
    rf = [0] * 32
    d_mem = [0] * 32


    # Run simulation until all instructions are processed.
    while True:
        instr = Fetch(program)
        if instr is None:
            break
        decoded = Decode(instr)
        signals = ControlUnit(decoded)
        alu_result = Execute(decoded, signals)
        mem_data = Mem(alu_result, decoded, signals)
        Writeback(decoded, signals, alu_result, mem_data)
    
    print("program terminated:")
    print(f"total execution time is {total_clock_cycles} cycles")

if __name__ == "__main__":
    main()

        