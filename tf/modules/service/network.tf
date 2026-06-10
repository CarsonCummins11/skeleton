data "aws_availability_zones" "available" {}

resource "aws_vpc" "main" {
    cidr_block = "172.17.0.0/16"
}

resource "aws_subnet" "private" {
    count             = 2
    cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index)
    availability_zone = data.aws_availability_zones.available.names[count.index]
    vpc_id            = aws_vpc.main.id
}


resource "aws_subnet" "public" {
    count                   = 2
    cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, 2 + count.index)
    availability_zone       = data.aws_availability_zones.available.names[count.index]
    vpc_id                  = aws_vpc.main.id
    map_public_ip_on_launch = true
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}