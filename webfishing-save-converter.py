import struct
import json
import argparse
import sys
from enum import IntEnum
from typing import Any, Dict, List, Union, BinaryIO

class GodotVariantType(IntEnum):
    NIL = 0
    BOOL = 1
    INT = 2
    REAL = 3
    STRING = 4
    VECTOR2 = 5
    RECT2 = 6
    VECTOR3 = 7
    TRANSFORM2D = 8
    PLANE = 9
    QUAT = 10
    AABB = 11
    BASIS = 12
    TRANSFORM = 13
    COLOR = 14
    NODE_PATH = 15
    RID = 16
    OBJECT = 17
    DICTIONARY = 18
    ARRAY = 19
    POOL_BYTE_ARRAY = 20
    POOL_INT_ARRAY = 21
    POOL_REAL_ARRAY = 22
    POOL_STRING_ARRAY = 23
    POOL_VECTOR2_ARRAY = 24
    POOL_VECTOR3_ARRAY = 25
    POOL_COLOR_ARRAY = 26

class SaveFileReader:
    def __init__(self, data: bytes):
        self.data = data
        self.position = 0
        
    def read_uint32(self) -> int:
        value = struct.unpack('<I', self.data[self.position:self.position + 4])[0]
        self.position += 4
        return value
    
    def read_int32(self) -> int:
        value = struct.unpack('<i', self.data[self.position:self.position + 4])[0]
        self.position += 4
        return value
    
    def read_int64(self) -> int:
        value = struct.unpack('<q', self.data[self.position:self.position + 8])[0]
        self.position += 8
        return value
    
    def read_float(self) -> float:
        value = struct.unpack('<f', self.data[self.position:self.position + 4])[0]
        self.position += 4
        return value
    
    def read_double(self) -> float:
        value = struct.unpack('<d', self.data[self.position:self.position + 8])[0]
        self.position += 8
        return value
    
    def read_string(self, length: int) -> str:
        value = self.data[self.position:self.position + length].decode('utf-8', errors='ignore')
        self.position += length
        return value
    
    def advance(self, count: int):
        self.position += count

class SaveFileWriter:
    def __init__(self):
        self.data = bytearray()

    def write_uint32(self, value: int):
        self.data.extend(struct.pack('<I', value))

    def write_int32(self, value: int):
        self.data.extend(struct.pack('<i', value))

    def write_int64(self, value: int):
        self.data.extend(struct.pack('<q', value))

    def write_float(self, value: float):
        self.data.extend(struct.pack('<f', value))

    def write_double(self, value: float):
        self.data.extend(struct.pack('<d', value))

    def write_string(self, value: str):
        encoded = value.encode('utf-8')
        self.write_uint32(len(encoded))
        self.data.extend(encoded)
        padding = b'\x00' * ((4 - len(encoded) % 4) % 4)
        self.data.extend(padding)

    def get_data(self) -> bytes:
        return bytes(self.data)

class WebFishingDeserializer:
    def __init__(self, buffer: bytes):
        self.reader = SaveFileReader(buffer)
        size = self.reader.read_uint32()
        if size < 4:
            raise RuntimeError("Invalid save file")
            
    def align_value(self, value: int, alignment: int) -> int:
        return ((value + alignment - 1) // alignment) * alignment
    
    def read_value(self) -> Any:
        type_val = self.reader.read_uint32()
        base_type = type_val & 0xFFFF
        flag = type_val >> 16
        
        if base_type == GodotVariantType.NIL:
            return None
            
        elif base_type == GodotVariantType.BOOL:
            return self.reader.read_uint32() == 1
            
        elif base_type == GodotVariantType.INT:
            if flag == 0:
                return self.reader.read_int32()
            return self.reader.read_int64()
            
        elif base_type == GodotVariantType.REAL:
            if flag == 0:
                return self.reader.read_float()
            return self.reader.read_double()
            
        elif base_type == GodotVariantType.STRING:
            length = self.reader.read_uint32()
            padded_length = self.align_value(length, 4)
            string = self.reader.read_string(length)
            self.reader.advance(padded_length - length)
            return string
            
        elif base_type == GodotVariantType.VECTOR2:
            return {
                "x": self.reader.read_float(),
                "y": self.reader.read_float()
            }
            
        elif base_type == GodotVariantType.DICTIONARY:
            result = {}
            size = self.reader.read_uint32()
            for _ in range(size):
                key_val = self.read_value()
                if isinstance(key_val, str):
                    key = key_val
                elif isinstance(key_val, int):
                    key = f"0x{key_val:08X}"
                else:
                    raise RuntimeError(f"Invalid dictionary key type: {type(key_val)}")
                result[key] = self.read_value()
            return result
            
        elif base_type == GodotVariantType.ARRAY:
            result = []
            size = self.reader.read_uint32()
            for _ in range(size):
                result.append(self.read_value())
            return result
        
        else:
            print(f"Skipping unsupported type: {base_type}")
            return f"Unsupported type {base_type}"

class WebFishingSerializer:
    def __init__(self):
        self.writer = SaveFileWriter()

    def align_value(self, value: int, alignment: int) -> int:
        return ((value + alignment - 1) // alignment) * alignment

    def write_value(self, value: Any):
        if value is None:
            self.writer.write_uint32(GodotVariantType.NIL)
        elif isinstance(value, bool):
            self.writer.write_uint32(GodotVariantType.BOOL)
            self.writer.write_uint32(1 if value else 0)
        elif isinstance(value, int):
            if -2**31 <= value <= 2**31-1:
                self.writer.write_uint32(GodotVariantType.INT)
                self.writer.write_int32(value)
            else:
                self.writer.write_uint32(GodotVariantType.INT | (1 << 16))
                self.writer.write_int64(value)
        elif isinstance(value, float):
            self.writer.write_uint32(GodotVariantType.REAL | (1 << 16))
            self.writer.write_double(value)
        elif isinstance(value, str):
            self.writer.write_uint32(GodotVariantType.STRING)
            self.writer.write_string(value)
        elif isinstance(value, dict):
            if len(value) == 2 and "x" in value and "y" in value:
                self.writer.write_uint32(GodotVariantType.VECTOR2)
                self.writer.write_float(value["x"])
                self.writer.write_float(value["y"])
            else:
                self.writer.write_uint32(GodotVariantType.DICTIONARY)
                self.writer.write_uint32(len(value))
                for k, v in value.items():
                    if k.startswith("0x"):
                        self.write_value(int(k, 16))
                    else:
                        self.write_value(k)
                    self.write_value(v)
        elif isinstance(value, list):
            self.writer.write_uint32(GodotVariantType.ARRAY)
            self.writer.write_uint32(len(value))
            for item in value:
                self.write_value(item)
        else:
            raise ValueError(f"Unsupported type: {type(value)}")

    def serialize(self, data: Dict) -> bytes:
        self.write_value(data)
        full_data = SaveFileWriter()
        full_data.write_uint32(len(self.writer.get_data()) + 4)
        full_data.data.extend(self.writer.get_data())
        return full_data.get_data()

def parse_save_file(file_path: str) -> Dict:
    """Parse a WebFishing save file and return its contents as a dictionary."""
    with open(file_path, 'rb') as f:
        data = f.read()
    
    deserializer = WebFishingDeserializer(data)
    return deserializer.read_value()

def convert_json_to_sav(json_file: str, sav_file: str):
    """Convert a JSON file to a WebFishing save file."""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    serializer = WebFishingSerializer()
    sav_data = serializer.serialize(data)

    with open(sav_file, 'wb') as f:
        f.write(sav_data)

def main():
    parser = argparse.ArgumentParser(description="WebFishing Save File Tool - Convert between .sav and JSON formats")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Decode command
    decode_parser = subparsers.add_parser('decode', help='Convert .sav file to JSON')
    decode_parser.add_argument("input_file", help="Path to the input .sav file")
    decode_parser.add_argument("output_file", help="Path to the output JSON file")
    decode_parser.add_argument("-i", "--info", action="store_true", help="Print basic player stats")

    # Encode command
    encode_parser = subparsers.add_parser('encode', help='Convert JSON file to .sav')
    encode_parser.add_argument("input_file", help="Path to the input JSON file")
    encode_parser.add_argument("output_file", help="Path to the output .sav file")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'decode':
            save_data = parse_save_file(args.input_file)
            with open(args.output_file, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4)
                
            print(f"Successfully decoded save file and wrote to {args.output_file}")

            if args.info:
                print("\nPlayer Stats:")
                print(f"Level: {save_data.get('level', 'N/A')}")
                print(f"XP: {save_data.get('xp', 'N/A')}")
                print(f"Money: {save_data.get('money', 'N/A')}")
                print(f"Fish Caught: {save_data.get('fish_caught', 'N/A')}")

        elif args.command == 'encode':
            convert_json_to_sav(args.input_file, args.output_file)
            print(f"Successfully encoded JSON to save file: {args.output_file}")

    except Exception as e:
        print(f"Error processing file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()